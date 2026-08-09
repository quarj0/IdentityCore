import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.providers.ai_service import AIServiceUnavailable
from apps.providers.adapters import (
    PROVIDER_CONTRACT_VERSION,
    normalize_provider_result,
)

from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderAssignment,
    ProviderAssignmentKey,
    ProviderAssignmentStatus,
    ProviderRoute,
    ProviderRouteStatus,
    ProviderStatus,
    ProviderType,
)
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


@dataclass(frozen=True)
class ProviderRouteResolution:
    route: ProviderRoute | None
    providers: tuple[Provider, ...]


def publish_provider_route(route: ProviderRoute) -> ProviderRoute:
    """Publish one immutable version and retire the prior version of its route key."""
    with transaction.atomic():
        Tenant.objects.select_for_update().get(pk=route.tenant_id)
        locked = ProviderRoute.objects.select_for_update().get(pk=route.pk)
        if locked.status != ProviderRouteStatus.DRAFT:
            raise ValidationError("Only draft provider routes can be published.")
        steps = list(locked.steps.select_related("provider").order_by("position"))
        if not steps:
            raise ValidationError(
                "A provider route requires at least one provider step."
            )
        if any(step.provider.status != ProviderStatus.ACTIVE for step in steps):
            raise ValidationError("Every provider in a published route must be active.")
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
    latest_document = verification.identity_documents.order_by("-created_at").first()
    return resolve_provider_chain(
        tenant=verification.tenant,
        environment=(
            verification.project.environment if verification.project_id else "sandbox"
        ),
        check_type=check_type,
        country_code=(
            metadata.get("country_code")
            or (latest_document.country_profile_id if latest_document else "")
        ),
        document_type=(
            metadata.get("document_type")
            or (latest_document.document_type_id if latest_document else "")
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
    provider_check.request_metadata_json = redact_provider_metadata(
        request_metadata or provider_check.request_metadata_json or {}
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
        provider_check.error_message = str(exc)
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
                "retryable": isinstance(exc, AIServiceUnavailable),
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
        persisted_request_metadata["provider_route_id"] = resolution.route.public_id
        persisted_request_metadata["provider_route_version"] = resolution.route.version
        persisted_request_metadata["provider_route_step"] = 1
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
