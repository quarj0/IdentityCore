from django.utils import timezone

from apps.webhooks.models import WebhookEndpoint, WebhookEvent


def queue_webhook_events(*, tenant, event_type: str, payload: dict) -> list[WebhookEvent]:
    queued = []
    for endpoint in tenant.webhook_endpoints.filter(status="active"):
        if event_type not in endpoint.events:
            continue
        event_payload = {
            "id": None,
            "type": event_type,
            "created_at": timezone.now().isoformat(),
            "data": payload,
        }
        webhook_event = WebhookEvent.objects.create(
            tenant=tenant,
            webhook_endpoint=endpoint,
            event_type=event_type,
            payload_json=event_payload,
        )
        event_payload["id"] = webhook_event.public_id
        webhook_event.payload_json = event_payload
        webhook_event.save(update_fields=["payload_json", "updated_at"])
        queued.append(webhook_event)
    return queued
