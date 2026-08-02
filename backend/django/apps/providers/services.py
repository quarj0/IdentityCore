import time
from collections.abc import Callable, Mapping
from typing import Any

from django.utils import timezone

from apps.providers.ai_service import AIServiceUnavailable

from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderAssignment,
    ProviderAssignmentKey,
    ProviderAssignmentStatus,
    ProviderStatus,
    ProviderType,
)


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
        if not isinstance(result, dict):
            raise TypeError("Provider operations must return a dictionary result.")
        normalized = normalize(result) if normalize else result
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


def resolve_provider_for_check(*, tenant, check_type: str) -> Provider:
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
    provider = resolve_provider_for_check(
        tenant=verification.tenant,
        check_type=check_type,
    )
    completed_at = now if status == ProviderCheckStatus.COMPLETED else None
    return ProviderCheck.objects.create(
        tenant=verification.tenant,
        verification=verification,
        provider=provider,
        check_type=check_type,
        status=status,
        provider_reference=provider_reference,
        request_metadata_json=request_metadata or {},
        response_metadata_json=response_metadata or {},
        normalized_result_json=normalized_result or {},
        started_at=now,
        completed_at=completed_at,
    )
