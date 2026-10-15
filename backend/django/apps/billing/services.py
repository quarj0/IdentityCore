"""Financially conservative, tenant-scoped invoice and payment state transitions."""
import calendar
import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.billing import paystack
from apps.billing.models import (
    BillingInvoice, BillingInvoiceLine, BillingMeter, BillingPayment,
    BillingPaymentEvent, BillingRefund, BillingPlan, BillingSubscription, BillingUsageEvent,
)


class BillingError(ValueError):
    pass


def _period(month):
    if not isinstance(month, str) or len(month) != 7 or month[4] != "-":
        raise BillingError("Month must be YYYY-MM")
    try:
        start = date.fromisoformat(month + "-01")
    except ValueError as exc:
        raise BillingError("Month must be YYYY-MM") from exc
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    if end > timezone.now().date().replace(day=1):
        raise BillingError("Invoice period is not closed")
    return start, end


@transaction.atomic
def generate_invoice(tenant, month):
    """An invoice for an already-closed calendar month; never silently default rates."""
    start, end = _period(month)
    subscription = (
        BillingSubscription.objects.select_for_update()
        .select_related("plan")
        .filter(tenant=tenant, status="active", deleted_at__isnull=True).first()
    )
    if not subscription or not subscription.plan.published:
        raise BillingError("Active published billing plan required")
    if subscription.started_at.date() >= end:
        raise BillingError("Subscription was not active during the period")
    if BillingInvoice.objects.filter(tenant=tenant, period_start=start).exists():
        raise BillingError("Invoice for period already exists")
    plan = subscription.plan
    starts_at = datetime.combine(start, datetime.min.time(), dt_timezone.utc)
    ends_at = datetime.combine(end, datetime.min.time(), dt_timezone.utc)
    events = list(
        BillingUsageEvent.objects.select_for_update()
        .filter(
            tenant=tenant,
            environment="production",
            occurred_at__gte=max(starts_at, subscription.started_at),
            occurred_at__lt=ends_at,
            rating_state="unrated",
        )
        .select_related("provider_check__provider")
        .order_by("pk")
    )
    # Prevent silently skipping a previously rated event in this period.
    count = BillingUsageEvent.objects.filter(
        tenant=tenant,
        environment="production",
        occurred_at__gte=max(starts_at, subscription.started_at),
        occurred_at__lt=ends_at,
    ).count()
    if count != len(events):
        raise BillingError("Period contains previously rated or disputed usage")
    # A complete bill requires every eligible terminal provider check to have
    # passed the independent tenant-attribution usage reconciliation first.
    from apps.providers.models import ProviderCheck, ProviderCheckStatus
    eligible = ProviderCheck.objects.filter(
        tenant=tenant,
        verification__project__environment="production",
        completed_at__gte=max(starts_at, subscription.started_at),
        completed_at__lt=ends_at,
        status__in=[
            ProviderCheckStatus.COMPLETED,
            ProviderCheckStatus.FAILED,
            ProviderCheckStatus.TIMEOUT,
        ],
    ).count()
    if eligible != count:
        raise BillingError("Unreconciled provider checks block month close")
    rates = {
        (meter.provider_scope, meter.capability, meter.outcome): meter
        for meter in BillingMeter.objects.filter(plan=plan, deleted_at__isnull=True)
    }
    missing = [
        event for event in events
        if (event.provider_scope, event.capability, event.outcome) not in rates
    ]
    if missing:
        raise BillingError("Unpriced provider usage; plan needs explicit meters")
    # First partial month has no base charge; regular monthly cycles begin next month.
    base_minor = plan.monthly_price_minor if subscription.started_at.date() <= start else 0
    invoice = BillingInvoice.objects.create(
        tenant=tenant, subscription=subscription, plan_code=plan.code,
        plan_version=plan.version, currency=plan.currency,
        period_start=start, period_end=end, amount_minor=0,
    )
    total = base_minor
    if base_minor:
        BillingInvoiceLine.objects.create(
            invoice=invoice, description="Monthly infrastructure subscription",
            quantity=1, unit_price_minor=base_minor, amount_minor=base_minor,
        )
    for event in events:
        rate = rates[event.provider_scope, event.capability, event.outcome]
        cost = rate.unit_price_minor * event.quantity
        BillingInvoiceLine.objects.create(
            invoice=invoice, usage_event=event,
            description=f"{event.provider_scope} / {event.capability} / {event.outcome}",
            quantity=event.quantity, unit_price_minor=rate.unit_price_minor,
            amount_minor=cost,
        )
        event.rating_state = "rated"
        event.save(update_fields=["rating_state", "updated_at"])
        total += cost
    if total >= 10**14:
        raise BillingError("Invoice exceeds supported amount")
    invoice.amount_minor = total
    invoice.save(update_fields=["amount_minor", "updated_at"])
    return invoice


@transaction.atomic
def issue_invoice(invoice_id):
    invoice = BillingInvoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status != "draft":
        raise BillingError("Only draft invoices can be issued")
    if sum(line.amount_minor for line in invoice.lines.all()) != invoice.amount_minor:
        raise BillingError("Invoice lines do not match total")
    now = timezone.now()
    invoice.status = "paid" if invoice.amount_minor == 0 else "issued"
    invoice.issued_at = now
    invoice.due_at = now + timedelta(days=14)
    if invoice.amount_minor == 0:
        invoice.paid_at = now
    invoice.save(update_fields=["status", "issued_at", "due_at", "paid_at", "updated_at"])
    return invoice


def payments_enabled():
    return getattr(settings, "BILLING_PAYMENTS_ENABLED", False) is True


def begin_checkout(invoice, *, billing_email):
    if not payments_enabled():
        raise BillingError("Payment collection is not enabled")
    with transaction.atomic():
        locked = BillingInvoice.objects.select_for_update().get(pk=invoice.pk)
        if locked.status != "issued" or locked.amount_minor <= 0:
            raise BillingError("Only unpaid issued invoices can be paid")
        if locked.currency != "GHS":
            raise BillingError("Paystack checkout is configured for GHS")
        existing = locked.payments.filter(status="pending").order_by("-created_at").first()
        if existing and existing.checkout_url:
            return existing
        if existing and timezone.now() - existing.created_at < timedelta(minutes=2):
            raise BillingError("Checkout initialization is in progress")
        # Reuse the same reference after a timeout rather than silently producing
        # multiple potentially chargeable gateway payment attempts.
        if existing:
            payment = existing
        else:
            payment = BillingPayment.objects.create(
                invoice=locked, provider="paystack",
                reference="ic" + secrets.token_hex(18),
                amount_minor=locked.amount_minor, currency=locked.currency,
            )
    url = paystack.initialize(
        reference=payment.reference, email=billing_email,
        amount_minor=payment.amount_minor, currency=payment.currency,
    )
    with transaction.atomic():
        payment = BillingPayment.objects.select_for_update().get(pk=payment.pk)
        if payment.status != "pending":
            raise BillingError("Payment status changed during checkout")
        payment.checkout_url = url
        payment.save(update_fields=["checkout_url", "updated_at"])
    return payment


def confirm_gateway_payment(reference, *, evidence_digest=None):
    """Only a server-verified Paystack transaction may settle an invoice."""
    payment = BillingPayment.objects.select_related("invoice").filter(
        reference=reference, provider="paystack"
    ).first()
    if payment is None:
        raise BillingError("Unknown payment")
    verified = paystack.verify(reference=reference)
    if verified.get("status") != "success":
        return False
    if (
        verified.get("reference") != payment.reference
        or type(verified.get("amount")) is not int
        or verified["amount"] != payment.amount_minor
        or verified.get("currency") != payment.currency
        or not isinstance(verified.get("id"), int)
    ):
        raise BillingError("Gateway transaction does not match the invoice")
    transaction_id = str(verified["id"])
    with transaction.atomic():
        locked = BillingPayment.objects.select_for_update().get(pk=payment.pk)
        invoice = BillingInvoice.objects.select_for_update().get(pk=locked.invoice_id)
        if evidence_digest is not None and BillingPaymentEvent.objects.filter(
            payload_sha256=evidence_digest
        ).exclude(payment=locked).exists():
            raise BillingError("Webhook digest attributed to another payment")
        if locked.status == "paid":
            if locked.gateway_transaction_id != transaction_id:
                raise BillingError("Duplicate payment has different transaction ID")
            return True
        if invoice.status != "issued" or locked.status not in ("pending", "failed"):
            raise BillingError("Unexpected paid transaction: manual financial review required")
        if invoice.amount_minor != locked.amount_minor or invoice.currency != locked.currency:
            raise BillingError("Invoice changed since checkout")
        locked.status = "paid"
        locked.gateway_transaction_id = transaction_id
        locked.confirmed_at = timezone.now()
        locked.save(update_fields=["status", "gateway_transaction_id", "confirmed_at", "updated_at"])
        invoice.status = "paid"
        invoice.paid_at = locked.confirmed_at
        invoice.save(update_fields=["status", "paid_at", "updated_at"])
        if evidence_digest is not None:
            BillingPaymentEvent.objects.get_or_create(
                payload_sha256=evidence_digest,
                defaults={"payment": locked, "event_type": "charge.success"},
            )
    return True


def _reconcile_gateway_refund(event):
    """Refund notifications are never trusted without a matching provider lookup."""
    data = event["data"]
    reference = data.get("transaction_reference")
    refund_id = data.get("id")
    if not isinstance(reference, str) or not paystack.REFERENCE.fullmatch(reference):
        return False
    if type(refund_id) is not int or refund_id <= 0:
        # Some gateway events omit the refund ID. Leave for operator
        # reconciliation instead of inventing a refund record.
        return False
    payment = BillingPayment.objects.select_related("invoice").filter(
        reference=reference, status__in=("paid", "disputed"), provider="paystack"
    ).first()
    if payment is None or not payment.gateway_transaction_id:
        return False
    result = paystack.verify_refund(refund_id=refund_id)
    if (
        type(result.get("id")) is not int
        or result["id"] != refund_id
        or str(result.get("transaction")) != payment.gateway_transaction_id
        or result.get("currency") != payment.currency
        or type(result.get("amount")) is not int
        or not 0 < result["amount"] <= payment.amount_minor
        or result.get("status") not in ("pending", "processing", "processed", "failed")
    ):
        raise BillingError("Refund lookup failed transaction attribution")
    with transaction.atomic():
        locked = BillingPayment.objects.select_for_update().get(pk=payment.pk)
        invoice = BillingInvoice.objects.select_for_update().get(pk=locked.invoice_id)
        refunded_total = sum(
            x.amount_minor for x in locked.refunds.exclude(gateway_refund_id=str(refund_id))
            .filter(status__in=("pending", "completed"))
        )
        if refunded_total + result["amount"] > locked.amount_minor:
            raise BillingError("Refund total exceeds settled charge")
        refund, created = BillingRefund.objects.get_or_create(
            gateway_refund_id=str(refund_id),
            defaults={
                "payment": locked, "amount_minor": result["amount"],
                "status": "pending",
            },
        )
        if refund.payment_id != locked.pk or refund.amount_minor != result["amount"]:
            raise BillingError("Refund changed its payment attribution")
        new_status = (
            "completed" if result["status"] == "processed" else
            "failed" if result["status"] == "failed" else "pending"
        )
        if refund.status == "completed" and new_status != "completed":
            return True  # Ignore old out-of-order notifications.
        if refund.status != new_status:
            refund.status = new_status
            if new_status == "completed":
                refund.confirmed_at = timezone.now()
            refund.save(update_fields=["status", "confirmed_at", "updated_at"])
        if new_status == "completed":
            invoice.status = "disputed"
            invoice.save(update_fields=["status", "updated_at"])
            locked.status = "disputed"
            locked.save(update_fields=["status", "updated_at"])
    return True


def _record_gateway_dispute(event):
    reference = event["data"].get("reference")
    if not isinstance(reference, str) or not paystack.REFERENCE.fullmatch(reference):
        return False
    with transaction.atomic():
        payment = BillingPayment.objects.select_for_update().filter(
            reference=reference, status="paid"
        ).first()
        if payment is None:
            return False
        invoice = BillingInvoice.objects.select_for_update().get(pk=payment.invoice_id)
        payment.status = "disputed"
        payment.save(update_fields=["status", "updated_at"])
        invoice.status = "disputed"
        invoice.save(update_fields=["status", "updated_at"])
    return True


def receive_paystack_webhook(body, signature):
    if not paystack.valid_webhook(body, signature):
        raise BillingError("Invalid gateway webhook signature")
    try:
        event = json.loads(body)
    except ValueError as exc:
        raise BillingError("Malformed webhook") from exc
    if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
        raise BillingError("Malformed webhook")
    event_type = event.get("event")
    if event_type in ("refund.pending", "refund.processing", "refund.processed", "refund.failed"):
        return _reconcile_gateway_refund(event)
    if event_type == "charge.dispute.create":
        return _record_gateway_dispute(event)
    if event_type != "charge.success":
        return False
    reference = event["data"].get("reference")
    if not isinstance(reference, str) or not paystack.REFERENCE.fullmatch(reference):
        raise BillingError("Invalid payment reference")
    return confirm_gateway_payment(
        reference, evidence_digest=hashlib.sha256(body).hexdigest()
    )
