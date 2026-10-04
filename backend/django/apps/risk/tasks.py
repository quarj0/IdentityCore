from celery import shared_task
from django.utils import timezone

from apps.risk.models import ReuseFingerprint
from common.authorization import ServicePrincipal, require_service_access

FINGERPRINT_RETENTION_WORKER = ServicePrincipal(
    name="fingerprint-retention-worker",
    allowed_actions=frozenset({"risk.cleanup_fingerprints"}),
    allow_cross_tenant=True,
)


@shared_task(queue="retention")
def cleanup_reuse_fingerprints_task(limit=1000):
    require_service_access(
        FINGERPRINT_RETENTION_WORKER, action="risk.cleanup_fingerprints"
    )
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise ValueError("Cleanup batch must be between 1 and 10000.")
    ids = list(
        ReuseFingerprint.objects.filter(expires_at__lte=timezone.now())
        .order_by("expires_at", "pk")
        .values_list("pk", flat=True)[:limit]
    )
    return ReuseFingerprint.objects.filter(pk__in=ids).delete()[0] if ids else 0
