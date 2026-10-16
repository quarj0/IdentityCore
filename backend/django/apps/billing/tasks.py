"""Bounded billing reconciliation and gated month-close Celery tasks."""

from datetime import timedelta, datetime, timezone as dt_timezone
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Exists, OuterRef, F, Q

from apps.billing.models import BillingInvoice, BillingSubscription
from apps.billing.services import BillingError, generate_invoice, issue_invoice
from apps.billing.usage import BillingIntegrityError, reconcile_provider_usage_checks
from apps.providers.models import ProviderCheck, ProviderCheckStatus

# Celery discovers apps.billing.tasks; import the inbox task so workers also
# register its module-qualified name used by beat and queue routing.
from apps.billing.webhook_tasks import reconcile_billing_webhooks_task  # noqa: F401

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def reconcile_billing_usage_task(limit=200):
    if not getattr(settings, "BILLING_USAGE_CAPTURE_ENABLED", False):
        return 0
    if not 1 <= limit <= 1000:
        raise ValueError("Invalid billing batch limit")
    checks = list(
        ProviderCheck.objects.filter(
            verification__project__environment="production",
            completed_at__isnull=False,
            status__in=[
                ProviderCheckStatus.COMPLETED,
                ProviderCheckStatus.FAILED,
                ProviderCheckStatus.TIMEOUT,
            ],
            billing_usage_event__isnull=True,
            billing_reconciliation_issue__isnull=True,
        )
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    recorded, failed = reconcile_provider_usage_checks(checks)
    if failed:
        raise BillingIntegrityError(
            f"{failed} usage checks require review; {recorded} recorded"
        )
    return recorded


@shared_task(ignore_result=True)
def generate_closed_month_invoices_task(limit=100):
    """Run daily after the prior UTC month has closed; opt-in only."""
    if not getattr(settings, "BILLING_AUTO_INVOICE_ENABLED", False):
        return 0
    if not 1 <= limit <= 1000:
        raise ValueError("Invalid billing batch limit")
    today = timezone.now().date()
    previous_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    period_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    completed_period = BillingInvoice.objects.filter(
        tenant_id=OuterRef("tenant_id"),
        period_start=period_start,
    ).exclude(status="draft")
    # Exclude completed periods before applying the batch limit so early
    # subscriptions cannot permanently starve later tenants.
    subscriptions = (
        BillingSubscription.objects.filter(
            plan__published=True,
            deleted_at__isnull=True,
            started_at__date__lt=today.replace(day=1),
        )
        .filter(
            Q(
                periods__started_at__lt=datetime.combine(
                    today.replace(day=1), datetime.min.time(), dt_timezone.utc
                )
            )
            & (
                Q(periods__ended_at__isnull=True)
                | Q(
                    periods__ended_at__gt=datetime.combine(
                        period_start, datetime.min.time(), dt_timezone.utc
                    )
                )
            )
            | (
                Q(history_recorded_from__gt=F("started_at"))
                & Q(
                    history_recorded_from__gt=datetime.combine(
                        period_start, datetime.min.time(), dt_timezone.utc
                    )
                )
            )
        )
        .distinct()
        .annotate(period_complete=Exists(completed_period))
        .filter(
            period_complete=False,
        )
        .order_by(F("invoice_last_attempt_at").asc(nulls_first=True), "pk")
        .values_list("pk", flat=True)[:limit]
    )
    completed = 0
    failed = 0
    for subscription_id in list(subscriptions):
        # Match generate_invoice's subscription-first lock order. Generation
        # and issuance commit together; existing drafts can resume safely.
        try:
            with transaction.atomic():
                subscription = (
                    BillingSubscription.objects.select_for_update(of=("self",))
                    .select_related("tenant", "plan")
                    .get(pk=subscription_id)
                )
                if subscription.deleted_at or not subscription.plan.published:
                    continue
                invoice = (
                    BillingInvoice.objects.select_for_update()
                    .filter(
                        tenant=subscription.tenant,
                        period_start=period_start,
                    )
                    .first()
                )
                if invoice is not None and invoice.status != "draft":
                    continue
                if invoice is None:
                    invoice = generate_invoice(subscription.tenant, previous_month)
                issue_invoice(invoice.pk)
                completed += 1
        except BillingError:
            # Persist scheduling progress after rolling back this tenant's
            # accounting. Unattempted/older tenants move ahead next run.
            BillingSubscription.objects.filter(pk=subscription_id).update(
                invoice_last_attempt_at=timezone.now()
            )
            failed += 1
            logger.error(
                "Monthly invoice requires review for subscription %s",
                subscription_id,
            )
    if failed:
        raise BillingError(
            f"{failed} monthly invoices require review; {completed} completed"
        )
    return completed
