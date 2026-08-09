from celery import shared_task

from apps.webhooks.services import (
    deliver_webhook_event_by_id,
    process_pending_webhook_events,
)
from apps.webhooks.models import WebhookEvent
from common.authorization import ServicePrincipal, require_service_access

WEBHOOK_WORKER = ServicePrincipal(
    name="webhook-worker",
    allowed_actions=frozenset({"webhook.deliver", "webhook.process_pending"}),
    allow_cross_tenant=True,
)


@shared_task(queue="webhooks")
def process_pending_webhook_events_task(limit: int = 50) -> int:
    require_service_access(WEBHOOK_WORKER, action="webhook.process_pending")
    return process_pending_webhook_events(limit=limit)


@shared_task(queue="webhooks")
def deliver_webhook_event_task(webhook_event_id: str) -> str:
    webhook_event = WebhookEvent.objects.only("tenant_id").get(
        public_id=webhook_event_id
    )
    require_service_access(
        WEBHOOK_WORKER,
        action="webhook.deliver",
        resource=webhook_event,
    )
    event = deliver_webhook_event_by_id(webhook_event_id)
    return event.status
