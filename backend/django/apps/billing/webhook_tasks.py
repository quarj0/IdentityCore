"""Durable webhook reconciliation with leases shorter than a bounded retry cycle."""

from datetime import timedelta
import logging
import secrets

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.billing.exceptions import GatewayError
from apps.billing.models import BillingWebhookEvent
from apps.billing.services import BillingError, process_paystack_webhook_event

logger = logging.getLogger(__name__)
LEASE_SECONDS = 300


def reconcile_webhook(event_id):
    token = secrets.token_hex(16)
    with transaction.atomic():
        event = BillingWebhookEvent.objects.select_for_update().get(pk=event_id)
        now = timezone.now()
        if event.processed_at or (event.lease_until and event.lease_until > now):
            return None
        event.claim_token = token
        event.lease_until = now + timedelta(seconds=LEASE_SECONDS)
        event.last_attempt_at = now
        event.error_code = ""
        event.save(
            update_fields=[
                "claim_token",
                "lease_until",
                "last_attempt_at",
                "error_code",
            ]
        )
    # Keep network work outside the inbox lock so repeated HTTP deliveries can
    # acknowledge immediately, even while this worker is fetching many pages.
    owned = BillingWebhookEvent.objects.filter(pk=event_id, claim_token=token)
    try:
        data = (
            {"reference": event.reference, "transaction_reference": event.reference}
            if event.reference
            else {"id": event.resource_id}
        )
        if not process_paystack_webhook_event(
            event.event_type, data, event.evidence_digest
        ):
            raise BillingError("Gateway evidence is not yet confirmed")
    except (BillingError, GatewayError, SoftTimeLimitExceeded) as exc:
        owned.update(
            lease_until=None, claim_token="", error_code="gateway_reconciliation_failed"
        )
        logger.error("Billing webhook requires review: event %s", event_id)
        if isinstance(exc, SoftTimeLimitExceeded):
            raise
        return False
    return bool(
        owned.update(
            processed_at=timezone.now(), lease_until=None, claim_token="", error_code=""
        )
    )


# A hard-killed worker cannot outlive its lease. After a crash, periodic recovery
# retries the financial operations idempotently once that lease expires.
@shared_task(ignore_result=True, soft_time_limit=240, time_limit=270)
def reconcile_billing_webhooks_task(limit=10):
    if not getattr(settings, "PAYSTACK_SECRET_KEY", ""):
        return 0
    if not 1 <= limit <= 100:
        raise ValueError("Invalid webhook batch limit")
    ids = list(
        BillingWebhookEvent.objects.filter(processed_at__isnull=True)
        .filter(Q(lease_until__isnull=True) | Q(lease_until__lte=timezone.now()))
        .order_by(F("last_attempt_at").asc(nulls_first=True), "pk")
        .values_list("pk", flat=True)[:limit]
    )
    completed = failed = 0
    for event_id in ids:
        result = reconcile_webhook(event_id)
        completed += result is True
        failed += result is False
    if failed:
        raise BillingError(
            f"{failed} webhook receipts require review; {completed} reconciled"
        )
    return completed
