from celery import shared_task
from django.utils import timezone

from apps.api_clients.models import APIIdempotencyRecord
from common.authorization import ServicePrincipal, require_service_access


API_CLIENT_RETENTION_WORKER = ServicePrincipal(
    name="api-client-retention-worker",
    allowed_actions=frozenset({"api_client.idempotency.cleanup"}),
    allow_cross_tenant=True,
)


@shared_task(queue="retention")
def cleanup_expired_idempotency_records_task(limit: int = 1000) -> int:
    """Delete expired replay records, including encrypted response secrets."""

    require_service_access(
        API_CLIENT_RETENTION_WORKER,
        action="api_client.idempotency.cleanup",
    )
    record_ids = list(
        APIIdempotencyRecord.objects.filter(expires_at__lte=timezone.now())
        .order_by("expires_at")
        .values_list("id", flat=True)[:limit]
    )
    if not record_ids:
        return 0
    deleted, _ = APIIdempotencyRecord.objects.filter(id__in=record_ids).delete()
    return deleted
