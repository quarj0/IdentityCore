from django.utils import timezone

from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderStatus,
    ProviderType,
)


SYSTEM_PROVIDER_DEFAULTS = {
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
    provider = get_or_create_system_provider(check_type)
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
