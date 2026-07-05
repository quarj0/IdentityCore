import hmac
import json
import time
from datetime import timedelta
from hashlib import sha256
from urllib import error, request

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.webhooks.models import (
    WebhookDeliveryAttempt,
    WebhookEndpoint,
    WebhookEndpointStatus,
    WebhookEvent,
    WebhookEventStatus,
)


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


def _encode_payload(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _build_signature(signing_key: str, timestamp: str, payload_bytes: bytes) -> str:
    message = timestamp.encode("utf-8") + b"." + payload_bytes
    digest = hmac.new(signing_key.encode("utf-8"), message, sha256).hexdigest()
    return f"sha256={digest}"


def _send_webhook_request(*, webhook_event: WebhookEvent, payload_bytes: bytes, timestamp: str):
    signature = _build_signature(webhook_event.webhook_endpoint.signing_key, timestamp, payload_bytes)
    http_request = request.Request(
        webhook_event.webhook_endpoint.url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "IdentityCore-Webhooks/1.0",
            "X-IdentityCore-Event-Id": webhook_event.public_id,
            "X-IdentityCore-Event-Type": webhook_event.event_type,
            "X-IdentityCore-Timestamp": timestamp,
            "X-IdentityCore-Signature": signature,
        },
        method="POST",
    )
    started_at = time.monotonic()
    with request.urlopen(http_request, timeout=settings.WEBHOOK_DELIVERY_TIMEOUT_SECONDS) as response:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        return response.status, response.read().decode("utf-8", errors="replace"), duration_ms


def _calculate_next_retry(*, attempt_count: int):
    delay_seconds = settings.WEBHOOK_RETRY_BASE_SECONDS * (2 ** max(attempt_count - 1, 0))
    return timezone.now() + timedelta(seconds=delay_seconds)


def _record_delivery_attempt(
    *,
    webhook_event: WebhookEvent,
    status_code: int | None,
    response_body: str = "",
    error_message: str = "",
    duration_ms: int | None = None,
) -> WebhookDeliveryAttempt:
    return WebhookDeliveryAttempt.objects.create(
        webhook_event=webhook_event,
        status_code=status_code,
        response_body=response_body,
        error_message=error_message,
        duration_ms=duration_ms,
    )


def deliver_webhook_event(webhook_event: WebhookEvent) -> WebhookEvent:
    if webhook_event.status in {WebhookEventStatus.DELIVERED, WebhookEventStatus.CANCELLED}:
        return webhook_event

    if webhook_event.webhook_endpoint.status != WebhookEndpointStatus.ACTIVE:
        webhook_event.status = WebhookEventStatus.CANCELLED
        webhook_event.next_retry_at = None
        webhook_event.save(update_fields=["status", "next_retry_at", "updated_at"])
        return webhook_event

    if not webhook_event.webhook_endpoint.signing_key:
        webhook_event.status = WebhookEventStatus.FAILED
        webhook_event.attempt_count += 1
        webhook_event.last_attempt_at = timezone.now()
        webhook_event.next_retry_at = None
        webhook_event.save(update_fields=["status", "attempt_count", "last_attempt_at", "next_retry_at", "updated_at"])
        _record_delivery_attempt(
            webhook_event=webhook_event,
            status_code=None,
            error_message="Webhook endpoint signing key is unavailable.",
        )
        record_audit_event(
            tenant=webhook_event.tenant,
            action="webhook.delivery_failed",
            target_type="webhook_event",
            target_id=webhook_event.public_id,
            metadata={"event_type": webhook_event.event_type, "reason": "missing_signing_key"},
        )
        return webhook_event

    payload_bytes = _encode_payload(webhook_event.payload_json)
    timestamp = str(int(timezone.now().timestamp()))
    try:
        status_code, response_body, duration_ms = _send_webhook_request(
            webhook_event=webhook_event,
            payload_bytes=payload_bytes,
            timestamp=timestamp,
        )
        webhook_event.attempt_count += 1
        webhook_event.last_attempt_at = timezone.now()
        if 200 <= status_code < 300:
            webhook_event.status = WebhookEventStatus.DELIVERED
            webhook_event.next_retry_at = None
            webhook_event.save(
                update_fields=["status", "attempt_count", "last_attempt_at", "next_retry_at", "updated_at"]
            )
            _record_delivery_attempt(
                webhook_event=webhook_event,
                status_code=status_code,
                response_body=response_body,
                duration_ms=duration_ms,
            )
            record_audit_event(
                tenant=webhook_event.tenant,
                action="webhook.delivered",
                target_type="webhook_event",
                target_id=webhook_event.public_id,
                metadata={"event_type": webhook_event.event_type, "status_code": status_code},
            )
            return webhook_event

        _record_delivery_attempt(
            webhook_event=webhook_event,
            status_code=status_code,
            response_body=response_body,
            error_message="Non-success webhook response.",
            duration_ms=duration_ms,
        )
    except error.URLError as exc:
        webhook_event.attempt_count += 1
        webhook_event.last_attempt_at = timezone.now()
        _record_delivery_attempt(
            webhook_event=webhook_event,
            status_code=None,
            error_message=str(exc.reason if hasattr(exc, "reason") else exc),
        )
    except Exception as exc:
        webhook_event.attempt_count += 1
        webhook_event.last_attempt_at = timezone.now()
        _record_delivery_attempt(
            webhook_event=webhook_event,
            status_code=None,
            error_message=str(exc),
        )

    if webhook_event.attempt_count >= settings.WEBHOOK_MAX_ATTEMPTS:
        webhook_event.status = WebhookEventStatus.FAILED
        webhook_event.next_retry_at = None
        record_audit_event(
            tenant=webhook_event.tenant,
            action="webhook.delivery_failed",
            target_type="webhook_event",
            target_id=webhook_event.public_id,
            metadata={"event_type": webhook_event.event_type, "attempt_count": webhook_event.attempt_count},
        )
    else:
        webhook_event.status = WebhookEventStatus.PENDING
        webhook_event.next_retry_at = _calculate_next_retry(attempt_count=webhook_event.attempt_count)
    webhook_event.save(update_fields=["status", "attempt_count", "last_attempt_at", "next_retry_at", "updated_at"])
    return webhook_event


def deliver_webhook_event_by_id(webhook_event_id: str) -> WebhookEvent:
    webhook_event = WebhookEvent.objects.select_related("webhook_endpoint", "tenant").get(public_id=webhook_event_id)
    return deliver_webhook_event(webhook_event)


def get_due_webhook_events(*, limit: int = 50):
    now = timezone.now()
    return (
        WebhookEvent.objects.select_related("webhook_endpoint", "tenant")
        .filter(status=WebhookEventStatus.PENDING)
        .filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=now))
        .order_by("created_at")[:limit]
    )


def process_pending_webhook_events(*, limit: int = 50) -> int:
    processed = 0
    for webhook_event in get_due_webhook_events(limit=limit):
        deliver_webhook_event(webhook_event)
        processed += 1
    return processed
