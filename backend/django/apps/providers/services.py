from django.utils import timezone

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


def get_tenant_provider_assignment(tenant, assignment_key: str) -> ProviderAssignment | None:
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


def get_notification_provider_assignment(tenant, channel: str) -> ProviderAssignment | None:
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
