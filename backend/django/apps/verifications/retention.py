from django.db.models import Q

from apps.verifications.models import RetentionLegalHold


def active_retention_holds(now):
    return RetentionLegalHold.objects.filter(released_at__isnull=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )


def has_active_retention_hold(*, tenant_id, verification_id, now):
    return (
        active_retention_holds(now)
        .filter(tenant_id=tenant_id)
        .filter(Q(verification_id__isnull=True) | Q(verification_id=verification_id))
        .exists()
    )
