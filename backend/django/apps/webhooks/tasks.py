from celery import shared_task

from apps.webhooks.services import deliver_webhook_event_by_id, process_pending_webhook_events


@shared_task
def process_pending_webhook_events_task(limit: int = 50) -> int:
    return process_pending_webhook_events(limit=limit)


@shared_task
def deliver_webhook_event_task(webhook_event_id: str) -> str:
    event = deliver_webhook_event_by_id(webhook_event_id)
    return event.status
