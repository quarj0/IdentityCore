"""Financially conservative, tenant-scoped invoice and payment state transitions."""

import calendar
import hashlib
import json
import secrets
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.billing import paystack
from apps.billing.gateways import enabled_providers, gateway_for
from apps.billing.models import (
    BillingInvoice,
    BillingInvoiceLine,
    BillingMeter,
    BillingPayment,
    BillingPaymentEvent,
    BillingRefund,
    BillingDispute,
    BillingPlan,
    BillingSubscription,
    BillingUsageEvent,
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
        BillingSubscription.objects.select_for_update(of=("self",))
        .select_related("plan")
        .filter(tenant=tenant, deleted_at__isnull=True)
        .first()
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
    if max(starts_at, subscription.started_at) < subscription.history_recorded_from:
        raise BillingError("Subscription activity history requires operator review")
    windows = [
        (max(starts_at, period.started_at), min(ends_at, period.ended_at or ends_at))
        for period in subscription.periods.filter(started_at__lt=ends_at)
        .filter(Q(ended_at__isnull=True) | Q(ended_at__gt=starts_at))
        .order_by("started_at")
    ]
    windows = [(left, right) for left, right in windows if left < right]
    if not windows:
        raise BillingError("Subscription was not active during the period")

    def within(field):
        query = Q(pk__in=[])
        for left, right in windows:
            query |= Q(**{field + "__gte": left, field + "__lt": right})
        return query

    covered_until = starts_at
    for left, right in windows:
        if left > covered_until:
            break
        covered_until = max(covered_until, right)
    events = list(
        BillingUsageEvent.objects.select_for_update(of=("self",))
        .filter(
            tenant=tenant,
            environment="production",
            rating_state="unrated",
        )
        .filter(within("occurred_at"))
        .select_related("provider_check__provider")
        .order_by("pk")
    )
    # Prevent silently skipping a previously rated event in this period.
    count = (
        BillingUsageEvent.objects.filter(
            tenant=tenant,
            environment="production",
        )
        .filter(within("occurred_at"))
        .count()
    )
    if count != len(events):
        raise BillingError("Period contains previously rated or disputed usage")
    # A complete bill requires every eligible terminal provider check to have
    # passed the independent tenant-attribution usage reconciliation first.
    from apps.providers.models import ProviderCheck, ProviderCheckStatus

    eligible = (
        ProviderCheck.objects.filter(
            tenant=tenant,
            verification__project__environment="production",
            status__in=[
                ProviderCheckStatus.COMPLETED,
                ProviderCheckStatus.FAILED,
                ProviderCheckStatus.TIMEOUT,
            ],
        )
        .filter(within("completed_at"))
        .count()
    )
    if eligible != count:
        raise BillingError("Unreconciled provider checks block month close")
    from apps.billing.usage import BillingIntegrityError, record_provider_usage

    for event in events:
        try:
            current, _ = record_provider_usage(event.provider_check_id)
        except BillingIntegrityError as exc:
            raise BillingError("Usage facts no longer match provider evidence") from exc
        if current is None or current.pk != event.pk:
            raise BillingError("Usage facts no longer match provider evidence")
    rates = {
        (meter.provider_scope, meter.capability, meter.outcome): meter
        for meter in BillingMeter.objects.filter(plan=plan, deleted_at__isnull=True)
    }
    missing = [
        event
        for event in events
        if (event.provider_scope, event.capability, event.outcome) not in rates
    ]
    if missing:
        raise BillingError("Unpriced provider usage; plan needs explicit meters")
    # First partial month has no base charge; regular monthly cycles begin next month.
    base_minor = plan.monthly_price_minor if covered_until >= ends_at else 0
    invoice = BillingInvoice.objects.create(
        tenant=tenant,
        subscription=subscription,
        plan_code=plan.code,
        plan_version=plan.version,
        currency=plan.currency,
        period_start=start,
        period_end=end,
        amount_minor=0,
    )
    total = base_minor
    if base_minor:
        BillingInvoiceLine.objects.create(
            invoice=invoice,
            description="Monthly infrastructure subscription",
            quantity=1,
            unit_price_minor=base_minor,
            amount_minor=base_minor,
        )
    for event in events:
        rate = rates[event.provider_scope, event.capability, event.outcome]
        cost = rate.unit_price_minor * event.quantity
        BillingInvoiceLine.objects.create(
            invoice=invoice,
            usage_event=event,
            description=f"{event.provider_scope} / {event.capability} / {event.outcome}",
            quantity=event.quantity,
            unit_price_minor=rate.unit_price_minor,
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
def generate_or_resume_draft_invoice(tenant, month):
    """Serialize month close with generation and resume an unissued invoice."""
    start, _ = _period(month)
    # Match the subscription-first lock order used by generation and the worker.
    BillingSubscription.objects.select_for_update().filter(tenant=tenant).first()
    existing = (
        BillingInvoice.objects.select_for_update()
        .filter(
            tenant=tenant,
            period_start=start,
        )
        .first()
    )
    if existing is not None:
        if existing.status != "draft":
            raise BillingError("Invoice for period is already issued")
        return existing
    return generate_invoice(tenant, month)


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
    invoice.save(
        update_fields=["status", "issued_at", "due_at", "paid_at", "updated_at"]
    )
    return invoice


def payments_enabled():
    return getattr(settings, "BILLING_PAYMENTS_ENABLED", False) is True


@contextmanager
def _payment_transaction(payment):
    with transaction.atomic():
        lock_audit_chain(payment.invoice.tenant_id)
        invoice = BillingInvoice.objects.select_for_update().get(pk=payment.invoice_id)
        locked = BillingPayment.objects.select_for_update().get(pk=payment.pk)
        yield locked, invoice


def _record_payment_event(payment, digest, event_type, event_id=""):
    if digest is None:
        return
    existing = BillingPaymentEvent.objects.filter(payload_sha256=digest).first()
    if existing is None and event_id:
        existing = BillingPaymentEvent.objects.filter(
            provider=payment.provider, gateway_event_id=event_id
        ).first()
    if existing is not None:
        if (
            existing.payment_id != payment.pk
            or existing.provider != payment.provider
            or existing.event_type != event_type
        ):
            raise BillingError("Gateway event changed its payment attribution")
        return
    try:
        with transaction.atomic():
            BillingPaymentEvent.objects.create(
                payment=payment,
                provider=payment.provider,
                payload_sha256=digest,
                event_type=event_type,
                gateway_event_id=event_id,
            )
    except IntegrityError as exc:
        raise BillingError("Gateway event is already attributed") from exc


def begin_checkout(invoice, *, billing_email, provider=None):
    provider = provider or "paystack"
    if not isinstance(provider, str) or provider not in enabled_providers(
        invoice.currency
    ):
        raise BillingError(
            "This payment provider is not enabled for the invoice currency"
        )
    adapter = gateway_for(provider)
    with transaction.atomic():
        lock_audit_chain(invoice.tenant_id)
        locked = BillingInvoice.objects.select_for_update().get(pk=invoice.pk)
        if locked.status != "issued" or locked.amount_minor <= 0:
            raise BillingError("Only unpaid issued invoices can be paid")
        if provider not in enabled_providers(locked.currency):
            raise BillingError("This provider does not support the invoice currency")
        existing = (
            locked.payments.filter(status="pending").order_by("-created_at").first()
        )
        if existing is not None and existing.provider != provider:
            raise BillingError(
                "Continue or reconcile the existing checkout before changing payment provider"
            )
        if existing is not None and existing.checkout_url:
            return existing
        if existing is not None and timezone.now() - existing.created_at < timedelta(
            minutes=2
        ):
            raise BillingError("Checkout initialization is in progress")
        if existing is not None:
            existing.status = "failed"
            existing.save(update_fields=["status", "updated_at"])
        payment = BillingPayment.objects.create(
            invoice=locked,
            provider=provider,
            reference="ic" + secrets.token_hex(18),
            amount_minor=locked.amount_minor,
            currency=locked.currency,
        )
    initialized = adapter.initialize(
        reference=payment.reference,
        email=billing_email,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        payment_id=payment.public_id,
    )
    url = initialized
    with _payment_transaction(payment) as (locked, current_invoice):
        if locked.status not in ("pending", "paid"):
            raise BillingError("Payment status changed during checkout")
        if (
            locked.amount_minor != current_invoice.amount_minor
            or locked.currency != current_invoice.currency
        ):
            raise BillingError("Invoice changed during checkout")
        locked.checkout_url = url
        locked.save(update_fields=["checkout_url", "updated_at"])
        return locked


def confirm_gateway_payment(
    reference,
    *,
    provider=None,
    evidence_digest=None,
    event_type="charge.success",
    event_id="",
):
    """Settle only an independently fetched transaction matching the invoice."""
    payment = (
        BillingPayment.objects.select_related("invoice")
        .filter(reference=reference)
        .first()
    )
    if payment is None or (provider is not None and payment.provider != provider):
        raise BillingError("Unknown payment")
    adapter = gateway_for(payment.provider)
    verified = adapter.verify(reference=reference)
    if (
        verified.get("reference") != payment.reference
        or type(verified.get("amount")) is not int
        or verified["amount"] != payment.amount_minor
        or verified.get("currency") != payment.currency
    ):
        raise BillingError("Gateway transaction does not match the invoice")
    state = verified.get("status")
    if state not in (
        "success",
        "failed",
        "abandoned",
        "pending",
        "ongoing",
        "processing",
        "queued",
        "reversed",
    ):
        raise BillingError("Unknown gateway payment state")
    transaction_id = verified.get("id")
    if state == "success":
        if type(transaction_id) is not int or transaction_id <= 0:
            raise BillingError("Paystack transaction ID is invalid")
        transaction_id = str(transaction_id)
    with _payment_transaction(payment) as (locked, invoice):
        if state in ("failed", "abandoned", "reversed"):
            if locked.status == "pending":
                locked.status = "failed"
                locked.save(update_fields=["status", "updated_at"])
            _record_payment_event(locked, evidence_digest, event_type, event_id)
            return False
        if state != "success":
            return False
        if locked.status in ("paid", "disputed", "partially_refunded", "refunded"):
            if locked.gateway_transaction_id != transaction_id:
                raise BillingError("Duplicate payment has different transaction ID")
            _record_payment_event(locked, evidence_digest, event_type, event_id)
            return True
        if invoice.status != "issued" or locked.status not in ("pending", "failed"):
            raise BillingError(
                "Unexpected paid transaction requires financial reconciliation"
            )
        if (
            invoice.amount_minor != locked.amount_minor
            or invoice.currency != locked.currency
        ):
            raise BillingError("Invoice changed since checkout")
        locked.status = "paid"
        locked.gateway_transaction_id = transaction_id
        locked.confirmed_at = timezone.now()
        try:
            with transaction.atomic():
                locked.save(
                    update_fields=[
                        "status",
                        "gateway_transaction_id",
                        "confirmed_at",
                        "updated_at",
                    ]
                )
        except IntegrityError as exc:
            raise BillingError(
                "Gateway transaction already settled another payment"
            ) from exc
        invoice.status = "paid"
        invoice.paid_at = locked.confirmed_at
        invoice.save(update_fields=["status", "paid_at", "updated_at"])
        _record_payment_event(locked, evidence_digest, event_type, event_id)
        record_audit_event(
            tenant=invoice.tenant,
            actor=None,
            action="billing.payment.confirmed",
            target_type="billing_payment",
            target_id=locked.public_id,
            metadata={"invoice_id": invoice.public_id, "provider": locked.provider},
        )
    return True


def _refresh_adjustment_state(payment, invoice):
    if payment.disputes.filter(status__in=("open", "lost")).exists():
        state = "disputed"
    else:
        total = sum(
            payment.refunds.filter(status="completed").values_list(
                "amount_minor", flat=True
            )
        )
        state = (
            "refunded"
            if total == payment.amount_minor
            else "partially_refunded" if total else "paid"
        )
    payment.status = invoice.status = state
    payment.save(update_fields=["status", "updated_at"])
    invoice.save(update_fields=["status", "updated_at"])


def reconcile_gateway_refund(provider, refund_id):
    result = gateway_for(provider).verify_refund(refund_id=refund_id)
    return _record_verified_refund(provider, refund_id, result)


def _record_verified_refund(provider, refund_id, result, *, expected_payment_id=None):
    """Consume only facts fetched through authenticated gateway adapters."""
    if not isinstance(result, dict):
        raise BillingError("Malformed verified refund")
    if type(result.get("id")) is not int or result["id"] != refund_id:
        raise BillingError("Paystack refund ID mismatch")
    transaction_id = result.get("transaction")
    if isinstance(transaction_id, dict):
        transaction_id = transaction_id.get("id")
    statuses = {
        "pending": "pending",
        "processing": "pending",
        "needs-attention": "pending",
        "processed": "completed",
        "failed": "failed",
    }
    if not isinstance(transaction_id, (str, int)) or isinstance(transaction_id, bool):
        raise BillingError("Refund transaction attribution is missing")
    payment = (
        BillingPayment.objects.select_related("invoice")
        .filter(
            provider=provider,
            gateway_transaction_id=str(transaction_id),
            status__in=("paid", "disputed", "partially_refunded", "refunded"),
        )
        .first()
    )
    if payment is None or (
        expected_payment_id is not None and payment.pk != expected_payment_id
    ):
        raise BillingError("Refund has no matching settled payment")
    new_status = statuses.get(result.get("status"))
    if (
        new_status is None
        or type(result.get("amount")) is not int
        or not 0 < result["amount"] <= payment.amount_minor
        or not isinstance(result.get("currency"), str)
        or result["currency"].upper() != payment.currency
    ):
        raise BillingError("Refund lookup failed amount or currency attribution")
    stored_id = provider + ":" + str(refund_id)
    with _payment_transaction(payment) as (locked, invoice):
        allocated = sum(
            locked.refunds.exclude(gateway_refund_id=stored_id)
            .filter(status__in=("pending", "completed"))
            .values_list("amount_minor", flat=True)
        )
        if allocated + result["amount"] > locked.amount_minor:
            raise BillingError("Refund total exceeds settled charge")
        refund, _ = BillingRefund.objects.get_or_create(
            gateway_refund_id=stored_id,
            defaults={
                "payment": locked,
                "amount_minor": result["amount"],
                "status": "pending",
            },
        )
        if refund.payment_id != locked.pk or refund.amount_minor != result["amount"]:
            raise BillingError("Refund changed its payment attribution")
        if refund.status != "completed":
            refund.status = new_status
            if new_status == "completed":
                refund.confirmed_at = timezone.now()
            refund.save(update_fields=["status", "confirmed_at", "updated_at"])
        _refresh_adjustment_state(locked, invoice)
    return True


def reconcile_gateway_dispute(provider, dispute_id):
    result = gateway_for(provider).verify_dispute(dispute_id=dispute_id)
    if result.get("id") != dispute_id:
        raise BillingError("Gateway dispute ID mismatch")
    transaction_data = result.get("transaction")
    if not isinstance(transaction_data, dict):
        raise BillingError("Paystack dispute transaction is missing")
    transaction_id = transaction_data.get("id")
    amount = result.get("refund_amount")
    if amount is None:
        amount = transaction_data.get("amount")
    currency = transaction_data.get("currency")
    if result.get("status") not in (
        "awaiting-merchant-feedback",
        "awaiting-bank-feedback",
        "pending",
        "resolved",
        "archived",
    ):
        raise BillingError("Unknown Paystack dispute state")
    state = "open"
    if result.get("status") in ("resolved", "archived"):
        if result.get("resolution") in ("merchant-accepted", "auto-accepted"):
            state = "lost"
        elif result.get("resolution") == "declined":
            state = "won"
    if not isinstance(transaction_id, (str, int)) or isinstance(transaction_id, bool):
        raise BillingError("Dispute transaction attribution is missing")
    payment = (
        BillingPayment.objects.select_related("invoice")
        .filter(
            provider=provider,
            gateway_transaction_id=str(transaction_id),
            status__in=("paid", "disputed", "partially_refunded", "refunded"),
        )
        .first()
    )
    if (
        payment is None
        or state is None
        or type(amount) is not int
        or not (0 <= amount <= payment.amount_minor and (amount > 0 or state == "won"))
        or not isinstance(currency, str)
        or currency.upper() != payment.currency
    ):
        raise BillingError("Dispute lookup failed payment attribution")
    with _payment_transaction(payment) as (locked, invoice):
        dispute, _ = BillingDispute.objects.get_or_create(
            gateway_dispute_id=provider + ":" + str(dispute_id),
            defaults={
                "payment": locked,
                "amount_minor": amount,
                "status": state,
                "gateway_status": result["status"],
            },
        )
        if dispute.payment_id != locked.pk:
            raise BillingError("Dispute changed its payment attribution")
        if dispute.status not in ("won", "lost"):
            dispute.amount_minor = amount
            dispute.status = state
            dispute.gateway_status = result["status"]
            dispute.save(
                update_fields=["amount_minor", "status", "gateway_status", "updated_at"]
            )
        _refresh_adjustment_state(locked, invoice)
    return True


def _reconcile_paystack_refund_event(data):
    reference = data.get("transaction_reference")
    if reference is None and type(data.get("id")) is int:
        # Older integrations may still provide the numeric refund identifier.
        return reconcile_gateway_refund("paystack", data["id"])
    if not isinstance(reference, str) or not paystack.REFERENCE.fullmatch(reference):
        raise BillingError("Invalid refund transaction reference")
    payment = BillingPayment.objects.filter(
        provider="paystack",
        reference=reference,
        status__in=("paid", "disputed", "partially_refunded", "refunded"),
    ).first()
    if payment is None or not payment.gateway_transaction_id.isdecimal():
        raise BillingError("Refund event has no settled Paystack transaction")
    rows = paystack.list_refunds(transaction_id=int(payment.gateway_transaction_id))
    if not rows:
        raise BillingError("Refund evidence is not yet available")
    # Null refund_reference is documented. Reconcile independently fetched
    # facts for this transaction, without guessing an ID from webhook amounts.
    with transaction.atomic():
        # Release failed reservations before crediting any newer refunds.
        rows = sorted(
            rows,
            key=lambda row: (
                0 if isinstance(row, dict) and row.get("status") == "failed" else 1
            ),
        )
        for result in rows:
            _record_verified_refund(
                "paystack",
                result.get("id") if isinstance(result, dict) else None,
                result,
                expected_payment_id=payment.pk,
            )
    return True


def _parse_paystack_webhook(body, signature):
    if not paystack.valid_webhook(body, signature):
        raise BillingError("Invalid gateway webhook signature")
    try:
        event = json.loads(body)
    except ValueError as exc:
        raise BillingError("Malformed webhook") from exc
    if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
        raise BillingError("Malformed webhook")
    if not isinstance(event.get("event"), str):
        raise BillingError("Malformed webhook event type")
    return event["event"], event["data"]


def process_paystack_webhook_event(event_type, data, evidence_digest):
    """Worker-only reconciliation using independently fetched gateway facts."""
    if event_type in (
        "refund.pending",
        "refund.processing",
        "refund.needs-attention",
        "refund.processed",
        "refund.failed",
    ):
        return _reconcile_paystack_refund_event(data)
    if event_type in (
        "charge.dispute.create",
        "charge.dispute.remind",
        "charge.dispute.resolve",
    ):
        return reconcile_gateway_dispute("paystack", data.get("id"))
    if event_type != "charge.success":
        return False
    reference = data.get("reference")
    if not isinstance(reference, str) or not paystack.REFERENCE.fullmatch(reference):
        raise BillingError("Invalid payment reference")
    return confirm_gateway_payment(
        reference, provider="paystack", evidence_digest=evidence_digest
    )


REFUND_WEBHOOK_EVENTS = frozenset(
    {
        "refund.pending",
        "refund.processing",
        "refund.needs-attention",
        "refund.processed",
        "refund.failed",
    }
)
DISPUTE_WEBHOOK_EVENTS = frozenset(
    {"charge.dispute.create", "charge.dispute.remind", "charge.dispute.resolve"}
)


def receive_paystack_webhook(body, signature):
    """Internal synchronous entry for callers outside the HTTP acknowledgement path."""
    event_type, data = _parse_paystack_webhook(body, signature)
    return process_paystack_webhook_event(
        event_type, data, hashlib.sha256(body).hexdigest()
    )


def enqueue_paystack_webhook(body, signature):
    """Acknowledge only after signature validation and a durable minimal receipt.

    No gateway or broker calls occur here. The periodic worker drains the inbox,
    including receipts accepted during a broker outage.
    """
    from apps.billing.models import BillingWebhookEvent

    event_type, data = _parse_paystack_webhook(body, signature)
    reference = ""
    resource_id = None
    if event_type == "charge.success":
        reference = data.get("reference")
    elif event_type in REFUND_WEBHOOK_EVENTS:
        reference = data.get("transaction_reference")
        if reference is None:
            reference = ""
            resource_id = data.get("id")
    elif event_type in DISPUTE_WEBHOOK_EVENTS:
        resource_id = data.get("id")
    else:
        return False
    if reference:
        if not isinstance(reference, str) or not paystack.REFERENCE.fullmatch(
            reference
        ):
            raise BillingError("Invalid webhook transaction reference")
    elif type(resource_id) is not int or not 0 < resource_id < 2**63:
        raise BillingError("Invalid webhook resource identifier")
    BillingWebhookEvent.objects.get_or_create(
        evidence_digest=hashlib.sha256(body).hexdigest(),
        defaults={
            "event_type": event_type,
            "reference": reference,
            "resource_id": resource_id,
        },
    )
    return True
