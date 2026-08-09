import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.providers.adapters import (
    PROVIDER_CONTRACT_VERSION,
    normalize_provider_result,
    provider_adapter_registry,
)

from apps.providers.models import (
    Provider,
    ProviderAttemptOutcome,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderAssignment,
    ProviderAssignmentKey,
    ProviderAssignmentStatus,
    ProviderCircuitState,
    ProviderCircuitStatus,
    ProviderExecutionAttempt,
    ProviderRoute,
    ProviderRouteFinalAction,
    ProviderRouteStep,
    ProviderRouteStatus,
    ProviderStatus,
    ProviderType,
)
from apps.core.models import generate_public_id
from apps.tenants.models import Tenant


SYSTEM_PROVIDER_DEFAULTS = {
    ProviderCheckType.DOCUMENT_OCR: {
        "code": "internal-document-ocr",
        "name": "Internal Document OCR Engine",
        "provider_type": ProviderType.DOCUMENT,
    },
    ProviderCheckType.DOCUMENT_CLASSIFICATION: {
        "code": "internal-document-classifier",
        "name": "Internal Document Classification Engine",
        "provider_type": ProviderType.DOCUMENT,
    },
    ProviderCheckType.DOCUMENT_QUALITY: {
        "code": "internal-document-quality",
        "name": "Internal Document Quality Engine",
        "provider_type": ProviderType.DOCUMENT,
    },
    ProviderCheckType.LIVENESS: {
        "code": "internal-liveness",
        "name": "Internal Liveness Engine",
        "provider_type": ProviderType.LIVENESS,
    },
    ProviderCheckType.FACE_MATCH: {
        "code": "internal-face-match",
        "name": "Internal Face Match Engine",
        "provider_type": ProviderType.BIOMETRIC,
    },
    ProviderCheckType.RISK_CHECK: {
        "code": "internal-risk-rules",
        "name": "Internal Risk Rules Engine",
        "provider_type": ProviderType.RISK,
    },
}

SENSITIVE_METADATA_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "document_storage_key",
        "password",
        "secret",
        "selfie_storage_key",
        "token",
    }
)

PROVIDER_CAPABILITY_METHODS = {
    ProviderCheckType.DOCUMENT_OCR: "document_ocr",
    ProviderCheckType.DOCUMENT_CLASSIFICATION: "document_classification",
    ProviderCheckType.DOCUMENT_QUALITY: "document_quality",
    ProviderCheckType.FACE_MATCH: "face_compare",
    ProviderCheckType.LIVENESS: "liveness",
}


@dataclass(frozen=True)
class ProviderRouteResolution:
    route: ProviderRoute | None
    providers: tuple[Provider, ...]


@dataclass(frozen=True)
class ProviderRouteExecutionResult:
    result: dict
    provider_check: ProviderCheck
    attempts: tuple[ProviderExecutionAttempt, ...]


class ProviderRouteExhausted(RuntimeError):
    """Safe terminal signal after every eligible route provider is exhausted."""

    error_code = "provider_route_exhausted"
    retryable = False
    public_message = "No provider could complete the requested capability."

    def __init__(self, *, final_action: str):
        super().__init__(self.public_message)
        self.final_action = final_action


def publish_provider_route(route: ProviderRoute) -> ProviderRoute:
    """Publish one immutable version and retire the prior version of its route key."""
    with transaction.atomic():
        Tenant.objects.select_for_update().get(pk=route.tenant_id)
        locked = ProviderRoute.objects.select_for_update().get(pk=route.pk)
        if locked.status != ProviderRouteStatus.DRAFT:
            raise ValidationError("Only draft provider routes can be published.")
        if locked.deleted_at is not None:
            raise ValidationError("Deleted provider routes cannot be published.")
        steps = list(locked.steps.select_related("provider").order_by("position"))
        if not steps:
            raise ValidationError(
                "A provider route requires at least one provider step."
            )
        if any(step.provider.status != ProviderStatus.ACTIVE for step in steps):
            raise ValidationError("Every provider in a published route must be active.")
        if any(step.deleted_at is not None for step in steps):
            raise ValidationError("Deleted provider route steps cannot be published.")
        for step in steps:
            # Route conditions and capability can change while a step is still
            # draft, so publication must revalidate the complete final graph.
            step.full_clean()
        latest_version = (
            ProviderRoute.objects.filter(
                tenant=locked.tenant,
                route_key=locked.route_key,
                environment=locked.environment,
            )
            .exclude(pk=locked.pk)
            .order_by("-version")
            .values_list("version", flat=True)
            .first()
        )
        if latest_version is not None and locked.version <= latest_version:
            raise ValidationError(
                "A published route version must increase monotonically."
            )
        ProviderRoute.objects.filter(
            tenant=locked.tenant,
            route_key=locked.route_key,
            environment=locked.environment,
            status=ProviderRouteStatus.ACTIVE,
        ).exclude(pk=locked.pk).update(
            status=ProviderRouteStatus.RETIRED,
            updated_at=timezone.now(),
        )
        published_at = timezone.now()
        ProviderRoute.objects.filter(pk=locked.pk).update(
            status=ProviderRouteStatus.ACTIVE,
            updated_at=published_at,
        )
        locked.status = ProviderRouteStatus.ACTIVE
        locked.updated_at = published_at
        route.status = ProviderRouteStatus.ACTIVE
        route.updated_at = published_at
        return locked


def _route_matches(
    route: ProviderRoute,
    *,
    country_code: str,
    document_type: str,
    workflow_public_id: str,
) -> bool:
    conditions = (
        (route.country_codes_json, country_code.upper()),
        (route.document_type_ids_json, document_type),
        (route.workflow_public_ids_json, workflow_public_id),
    )
    return all(
        not configured or value in configured for configured, value in conditions
    )


def _route_specificity(route: ProviderRoute) -> int:
    return sum(
        bool(values)
        for values in (
            route.country_codes_json,
            route.document_type_ids_json,
            route.workflow_public_ids_json,
        )
    )


def resolve_provider_chain(
    *,
    tenant,
    environment: str,
    check_type: str,
    country_code: str = "",
    document_type: str = "",
    workflow_public_id: str = "",
) -> ProviderRouteResolution:
    """Resolve one deterministic route and its ordered active provider chain."""
    candidates = list(
        ProviderRoute.objects.filter(
            tenant=tenant,
            environment=environment,
            capability=check_type,
            status=ProviderRouteStatus.ACTIVE,
        ).prefetch_related("steps__provider")
    )
    latest_by_key = {}
    for route in candidates:
        existing = latest_by_key.get(route.route_key)
        if existing is None or route.version > existing.version:
            latest_by_key[route.route_key] = route
    matching = [
        route
        for route in latest_by_key.values()
        if _route_matches(
            route,
            country_code=country_code,
            document_type=document_type,
            workflow_public_id=workflow_public_id,
        )
    ]
    matching.sort(
        key=lambda route: (
            -_route_specificity(route),
            route.priority,
            route.route_key,
            -route.version,
            route.public_id,
        )
    )
    for route in matching:
        providers = tuple(
            step.provider
            for step in route.steps.all()
            if step.provider.status == ProviderStatus.ACTIVE
            and step.provider.tenant_id in {None, tenant.id}
        )
        if providers:
            return ProviderRouteResolution(route=route, providers=providers)
    assignment = get_tenant_provider_assignment(tenant, check_type)
    provider = (
        assignment.provider
        if assignment is not None
        else get_or_create_system_provider(check_type)
    )
    return ProviderRouteResolution(route=None, providers=(provider,))


def resolve_provider_chain_for_verification(
    *, verification, check_type: str, request_metadata: dict | None = None
) -> ProviderRouteResolution:
    metadata = request_metadata or {}
    referenced_document = None
    if metadata.get("identity_document_id"):
        referenced_document = verification.identity_documents.filter(
            public_id=metadata["identity_document_id"]
        ).first()
    selected_document = (
        referenced_document
        or verification.identity_documents.order_by("-created_at").first()
    )
    return resolve_provider_chain(
        tenant=verification.tenant,
        environment=(
            verification.project.environment if verification.project_id else "sandbox"
        ),
        check_type=check_type,
        country_code=(
            metadata.get("country_code")
            or (selected_document.country_profile_id if selected_document else "")
        ),
        document_type=(
            metadata.get("document_type")
            or (selected_document.document_type_id if selected_document else "")
        ),
        workflow_public_id=(
            metadata.get("workflow_id")
            or (verification.workflow_snapshot_json or {}).get("workflow_id", "")
        ),
    )


def redact_provider_metadata(value: Any) -> Any:
    """Return telemetry-safe metadata without credentials or evidence locations."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if str(key).lower() in SENSITIVE_METADATA_KEYS
                else redact_provider_metadata(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_provider_metadata(item) for item in value]
    return value


def invoke_provider_check(
    *,
    provider_check: ProviderCheck,
    operation: Callable[..., dict],
    operation_kwargs: dict,
    request_metadata: dict | None = None,
    normalize: Callable[[dict], dict] | None = None,
) -> dict:
    """Resolve invocation bookkeeping through one normalized provider boundary.

    Provider failures are re-raised so workflow-specific retry/review behavior remains
    in the calling task, but the attempt is always completed and queryable first.
    """
    if provider_check is None:
        raise ValueError("A provider check is required for every provider invocation.")
    started_at = timezone.now()
    started_clock = time.monotonic()
    provider_check.status = ProviderCheckStatus.PROCESSING
    provider_check.started_at = started_at
    provider_check.completed_at = None
    merged_request_metadata = dict(provider_check.request_metadata_json or {})
    merged_request_metadata.update(request_metadata or {})
    provider_check.request_metadata_json = redact_provider_metadata(
        merged_request_metadata
    )
    provider_check.save(
        update_fields=[
            "status",
            "started_at",
            "completed_at",
            "request_metadata_json",
            "updated_at",
        ]
    )

    try:
        result = operation(**operation_kwargs)
        normalized = normalize(result) if normalize else result
        normalized = normalize_provider_result(provider_check.check_type, normalized)
    except Exception as exc:
        completed_at = timezone.now()
        error_code = getattr(exc, "error_code", "provider_error")
        status = getattr(exc, "provider_check_status", ProviderCheckStatus.FAILED)
        if status not in {ProviderCheckStatus.FAILED, ProviderCheckStatus.TIMEOUT}:
            status = ProviderCheckStatus.FAILED
        provider_check.status = status
        provider_check.completed_at = completed_at
        provider_check.duration_ms = max(
            0, round((time.monotonic() - started_clock) * 1000)
        )
        provider_check.error_code = error_code
        provider_check.error_message = getattr(
            exc, "public_message", "Provider invocation failed."
        )
        provider_check.response_metadata_json = {
            "outcome": status,
            "error_code": error_code,
        }
        provider_check.normalized_result_json = {
            "contract_version": PROVIDER_CONTRACT_VERSION,
            "capability": provider_check.check_type,
            "status": status,
            "error": {
                "code": error_code,
                "retryable": bool(getattr(exc, "retryable", False)),
            },
        }
        provider_check.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_ms",
                "error_code",
                "error_message",
                "response_metadata_json",
                "normalized_result_json",
                "updated_at",
            ]
        )
        raise

    provider_check.status = ProviderCheckStatus.COMPLETED
    provider_check.completed_at = timezone.now()
    provider_check.duration_ms = max(
        0, round((time.monotonic() - started_clock) * 1000)
    )
    provider_check.error_code = ""
    provider_check.error_message = ""
    provider_check.response_metadata_json = redact_provider_metadata(
        {
            "outcome": ProviderCheckStatus.COMPLETED,
            "model_name": result.get("model_name", ""),
            "model_version": result.get("model_version", ""),
            "engine": result.get("engine", ""),
        }
    )
    provider_check.normalized_result_json = normalized
    provider_check.save(
        update_fields=[
            "status",
            "completed_at",
            "duration_ms",
            "error_code",
            "error_message",
            "response_metadata_json",
            "normalized_result_json",
            "updated_at",
        ]
    )
    return normalized


def invoke_selected_provider_operation(
    *,
    provider: Provider,
    check_type: str,
    timeout_seconds: int,
    operation_kwargs: dict,
    built_in_operation: Callable[..., dict],
) -> dict:
    """Invoke the adapter belonging to the provider selected by the route."""
    system_code = SYSTEM_PROVIDER_DEFAULTS.get(check_type, {}).get("code")
    if provider.code == system_code:
        return built_in_operation(**operation_kwargs)
    adapter = provider_adapter_registry.resolve(provider.code)
    method_name = PROVIDER_CAPABILITY_METHODS.get(check_type)
    if method_name is None:
        raise LookupError(f"No provider capability method exists for {check_type!r}.")
    operation = getattr(adapter, method_name)
    return operation(timeout_seconds=timeout_seconds, **operation_kwargs)


def _claim_circuit_probe(route_step: ProviderRouteStep | None) -> str | None:
    if route_step is None:
        return "closed"
    now = timezone.now()
    with transaction.atomic():
        state, created = ProviderCircuitState.objects.get_or_create(
            route_step=route_step
        )
        if not created:
            state = ProviderCircuitState.objects.select_for_update().get(pk=state.pk)
        if state.status == ProviderCircuitStatus.CLOSED:
            return "closed"
        if state.status == ProviderCircuitStatus.HALF_OPEN:
            if state.retry_after is not None and state.retry_after <= now:
                state.retry_after = now + timedelta(
                    seconds=route_step.route.circuit_recovery_seconds
                )
                state.save(update_fields=["retry_after", "updated_at"])
                return "probe"
            return None
        if state.retry_after is not None and state.retry_after > now:
            return None
        state.status = ProviderCircuitStatus.HALF_OPEN
        state.retry_after = now + timedelta(
            seconds=route_step.route.circuit_recovery_seconds
        )
        state.save(update_fields=["status", "retry_after", "updated_at"])
        return "probe"


def _record_circuit_outcome(
    route_step: ProviderRouteStep | None,
    *,
    succeeded: bool,
    retryable: bool,
) -> None:
    if route_step is None:
        return
    now = timezone.now()
    with transaction.atomic():
        state, created = ProviderCircuitState.objects.get_or_create(
            route_step=route_step
        )
        if not created:
            state = ProviderCircuitState.objects.select_for_update().get(pk=state.pk)
        if succeeded:
            state.status = ProviderCircuitStatus.CLOSED
            state.consecutive_failures = 0
            state.opened_at = None
            state.retry_after = None
        elif retryable:
            state.consecutive_failures += 1
            if (
                state.status == ProviderCircuitStatus.HALF_OPEN
                or state.consecutive_failures
                >= route_step.route.circuit_failure_threshold
            ):
                state.status = ProviderCircuitStatus.OPEN
                state.opened_at = now
                state.retry_after = now + timedelta(
                    seconds=route_step.route.circuit_recovery_seconds
                )
        else:
            # A deterministic provider response proves transport recovery even when
            # the request itself is not retryable.
            state.status = ProviderCircuitStatus.CLOSED
            state.consecutive_failures = 0
            state.opened_at = None
            state.retry_after = None
        state.save(
            update_fields=[
                "status",
                "consecutive_failures",
                "opened_at",
                "retry_after",
                "updated_at",
            ]
        )


def _record_execution_attempt(
    *,
    provider_check: ProviderCheck,
    execution_id: str,
    route,
    route_step,
    sequence: int,
    provider_attempt: int,
    outcome: str,
    error_code: str = "",
    retryable: bool = False,
    fallback_reason: str = "",
    timeout_seconds: int,
    started_at,
) -> ProviderExecutionAttempt:
    return ProviderExecutionAttempt.objects.create(
        provider_check=provider_check,
        execution_id=execution_id,
        route=route,
        route_step=route_step,
        sequence=sequence,
        provider_attempt=provider_attempt,
        outcome=outcome,
        error_code=error_code,
        retryable=retryable,
        fallback_reason=fallback_reason,
        timeout_seconds=timeout_seconds,
        started_at=started_at,
        completed_at=timezone.now(),
    )


@transaction.atomic
def _apply_route_final_action(
    *, verification, route, check_type: str, attempts: list[ProviderExecutionAttempt]
) -> str:
    from apps.audit.services import record_audit_event
    from apps.notifications.services import queue_verification_status_notifications
    from apps.webhooks.services import queue_webhook_events
    from apps.verifications.models import (
        VerificationDecision,
        VerificationDecisionType,
        VerificationStatus,
    )
    from apps.verifications.transitions import transition_verification

    final_action = (
        route.final_action
        if route is not None
        else ProviderRouteFinalAction.MANUAL_REVIEW
    )
    target_status = (
        VerificationStatus.MANUAL_REVIEW_REQUIRED
        if final_action == ProviderRouteFinalAction.MANUAL_REVIEW
        else VerificationStatus.FAILED
    )
    now = timezone.now()
    transition_verification(
        verification,
        target_status,
        completed_at=now if target_status == VerificationStatus.FAILED else None,
        clear_completed_at=target_status == VerificationStatus.MANUAL_REVIEW_REQUIRED,
    )
    VerificationDecision.objects.update_or_create(
        verification=verification,
        defaults={
            "tenant": verification.tenant,
            "decision": target_status,
            "decision_type": VerificationDecisionType.SYSTEM,
            "reason_code": "provider_route_exhausted",
            "reason_detail": (
                "Automated providers could not complete the requested capability."
            ),
            "evidence_summary_json": {
                "capability": check_type,
                "provider_route_id": route.public_id if route is not None else "",
                "provider_route_version": route.version if route is not None else None,
                "attempt_count": len(attempts),
                "error_codes": list(
                    dict.fromkeys(
                        attempt.error_code for attempt in attempts if attempt.error_code
                    )
                ),
            },
            "decided_by": None,
            "decided_at": now,
        },
    )
    record_audit_event(
        tenant=verification.tenant,
        actor=verification.verification_subject,
        action=f"verification.{target_status}",
        target_type="verification",
        target_id=verification.public_id,
        metadata={
            "reason_code": "provider_route_exhausted",
            "capability": check_type,
            "provider_route_id": route.public_id if route is not None else "",
            "attempt_count": len(attempts),
        },
    )
    event_type = f"verification.{target_status}"
    queue_webhook_events(
        tenant=verification.tenant,
        event_type=event_type,
        payload={
            "verification_id": verification.public_id,
            "external_reference": verification.external_reference,
            "status": verification.status,
            "reason_code": "provider_route_exhausted",
        },
    )
    queue_verification_status_notifications(
        verification=verification,
        decision=verification.status,
        risk_level="high",
    )
    return final_action


def execute_provider_route(
    *,
    verification,
    check_type: str,
    operation: Callable[[Provider, int], dict],
    request_metadata: dict | None = None,
    initial_provider_check: ProviderCheck | None = None,
) -> ProviderRouteExecutionResult:
    """Execute bounded attempts across one resolved provider chain.

    ``operation`` receives the selected provider and the route timeout. Adapters must
    enforce that timeout at their I/O boundary.
    """
    resolution = resolve_provider_chain_for_verification(
        verification=verification,
        check_type=check_type,
        request_metadata=request_metadata,
    )
    route = resolution.route
    timeout_seconds = route.timeout_seconds if route is not None else 30
    max_attempts = route.max_attempts_per_provider if route is not None else 1
    route_steps = {
        step.provider_id: step
        for step in (route.steps.select_related("provider").all() if route else [])
    }
    attempts: list[ProviderExecutionAttempt] = []
    execution_id = generate_public_id("pex")
    sequence = 0
    last_exception: Exception | None = None

    for provider_index, provider in enumerate(resolution.providers):
        route_step = route_steps.get(provider.id)
        circuit_claim = _claim_circuit_probe(route_step)
        if not circuit_claim:
            sequence += 1
            now = timezone.now()
            skipped_check = ProviderCheck.objects.create(
                tenant=verification.tenant,
                verification=verification,
                provider=provider,
                check_type=check_type,
                status=ProviderCheckStatus.CANCELLED,
                request_metadata_json=redact_provider_metadata(request_metadata or {}),
                error_code="provider_circuit_open",
                error_message="Provider circuit is temporarily open.",
                normalized_result_json={
                    "contract_version": PROVIDER_CONTRACT_VERSION,
                    "capability": check_type,
                    "status": ProviderCheckStatus.CANCELLED,
                    "error": {"code": "provider_circuit_open", "retryable": True},
                },
                started_at=now,
                completed_at=now,
            )
            attempts.append(
                _record_execution_attempt(
                    provider_check=skipped_check,
                    execution_id=execution_id,
                    route=route,
                    route_step=route_step,
                    sequence=sequence,
                    provider_attempt=0,
                    outcome=ProviderAttemptOutcome.SKIPPED,
                    error_code="provider_circuit_open",
                    retryable=True,
                    fallback_reason="circuit_open",
                    timeout_seconds=timeout_seconds,
                    started_at=now,
                )
            )
            continue

        for provider_attempt in range(1, max_attempts + 1):
            sequence += 1
            started_at = timezone.now()
            check_metadata = dict(request_metadata or {})
            if route is not None:
                check_metadata.update(
                    {
                        "provider_route_id": route.public_id,
                        "provider_route_version": route.version,
                        "provider_route_step": route_step.position,
                    }
                )
            use_initial_check = (
                initial_provider_check is not None
                and provider_index == 0
                and provider_attempt == 1
                and initial_provider_check.provider_id == provider.id
                and not hasattr(initial_provider_check, "execution_attempt")
            )
            if use_initial_check:
                provider_check = initial_provider_check
            else:
                provider_check = ProviderCheck.objects.create(
                    tenant=verification.tenant,
                    verification=verification,
                    provider=provider,
                    check_type=check_type,
                    status=ProviderCheckStatus.PENDING,
                    request_metadata_json=redact_provider_metadata(check_metadata),
                    started_at=started_at,
                )
            try:
                result = invoke_provider_check(
                    provider_check=provider_check,
                    operation=lambda: operation(provider, timeout_seconds),
                    operation_kwargs={},
                    request_metadata=check_metadata,
                )
            except Exception as exc:
                last_exception = exc
                retryable = bool(getattr(exc, "retryable", False))
                error_code = getattr(exc, "error_code", "provider_error")
                has_retry = (
                    retryable
                    and circuit_claim != "probe"
                    and provider_attempt < max_attempts
                )
                has_fallback = provider_index + 1 < len(resolution.providers)
                fallback_reason = (
                    "retryable_error"
                    if has_retry
                    else "provider_fallback"
                    if has_fallback
                    else "route_exhausted"
                )
                attempt = _record_execution_attempt(
                    provider_check=provider_check,
                    execution_id=execution_id,
                    route=route,
                    route_step=route_step,
                    sequence=sequence,
                    provider_attempt=provider_attempt,
                    outcome=(
                        ProviderAttemptOutcome.TIMEOUT
                        if provider_check.status == ProviderCheckStatus.TIMEOUT
                        else ProviderAttemptOutcome.FAILED
                    ),
                    error_code=error_code,
                    retryable=retryable,
                    fallback_reason=fallback_reason,
                    timeout_seconds=timeout_seconds,
                    started_at=started_at,
                )
                attempts.append(attempt)
                _record_circuit_outcome(
                    route_step, succeeded=False, retryable=retryable
                )
                if has_retry:
                    continue
                break
            else:
                attempt = _record_execution_attempt(
                    provider_check=provider_check,
                    execution_id=execution_id,
                    route=route,
                    route_step=route_step,
                    sequence=sequence,
                    provider_attempt=provider_attempt,
                    outcome=ProviderAttemptOutcome.SUCCEEDED,
                    timeout_seconds=timeout_seconds,
                    started_at=started_at,
                )
                attempts.append(attempt)
                _record_circuit_outcome(route_step, succeeded=True, retryable=False)
                return ProviderRouteExecutionResult(
                    result=result,
                    provider_check=provider_check,
                    attempts=tuple(attempts),
                )

    if route is None and last_exception is not None:
        raise last_exception
    final_action = _apply_route_final_action(
        verification=verification,
        route=route,
        check_type=check_type,
        attempts=attempts,
    )
    raise ProviderRouteExhausted(final_action=final_action)


def get_or_create_system_provider(check_type: str) -> Provider:
    defaults = SYSTEM_PROVIDER_DEFAULTS[check_type]
    provider, _ = Provider.objects.get_or_create(
        code=defaults["code"],
        defaults={
            "name": defaults["name"],
            "provider_type": defaults["provider_type"],
            "status": ProviderStatus.ACTIVE,
        },
    )
    return provider


def get_tenant_provider_assignment(
    tenant, assignment_key: str
) -> ProviderAssignment | None:
    return (
        ProviderAssignment.objects.select_related("provider")
        .filter(
            tenant=tenant,
            assignment_key=assignment_key,
            status=ProviderAssignmentStatus.ACTIVE,
        )
        .first()
    )


def resolve_provider_for_check(
    *, tenant, check_type: str, verification=None, request_metadata: dict | None = None
) -> Provider:
    if verification is not None:
        return resolve_provider_chain_for_verification(
            verification=verification,
            check_type=check_type,
            request_metadata=request_metadata,
        ).providers[0]
    assignment = get_tenant_provider_assignment(tenant, check_type)
    if assignment is not None:
        return assignment.provider
    return get_or_create_system_provider(check_type)


def get_notification_provider_assignment(
    tenant, channel: str
) -> ProviderAssignment | None:
    assignment_key = {
        "email": ProviderAssignmentKey.NOTIFICATION_EMAIL,
        "sms": ProviderAssignmentKey.NOTIFICATION_SMS,
        "in_app": ProviderAssignmentKey.NOTIFICATION_IN_APP,
    }.get(channel)
    if assignment_key is None:
        return None
    return get_tenant_provider_assignment(tenant, assignment_key)


def create_provider_check(
    *,
    verification,
    check_type: str,
    status: str,
    normalized_result: dict | None = None,
    request_metadata: dict | None = None,
    response_metadata: dict | None = None,
    provider_reference: str = "",
) -> ProviderCheck:
    now = timezone.now()
    resolution = resolve_provider_chain_for_verification(
        verification=verification,
        check_type=check_type,
        request_metadata=request_metadata,
    )
    provider = resolution.providers[0]
    persisted_request_metadata = dict(request_metadata or {})
    if resolution.route is not None:
        selected_step = resolution.route.steps.get(provider=provider)
        persisted_request_metadata["provider_route_id"] = resolution.route.public_id
        persisted_request_metadata["provider_route_version"] = resolution.route.version
        persisted_request_metadata["provider_route_step"] = selected_step.position
    completed_at = now if status == ProviderCheckStatus.COMPLETED else None
    return ProviderCheck.objects.create(
        tenant=verification.tenant,
        verification=verification,
        provider=provider,
        check_type=check_type,
        status=status,
        provider_reference=provider_reference,
        request_metadata_json=persisted_request_metadata,
        response_metadata_json=response_metadata or {},
        normalized_result_json=normalized_result or {},
        started_at=now,
        completed_at=completed_at,
    )
