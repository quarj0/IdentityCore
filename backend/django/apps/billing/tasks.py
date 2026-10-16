"""Bounded billing reconciliation and gated month-close Celery tasks."""

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Exists, OuterRef

from apps.billing.models import BillingInvoice, BillingSubscription
from apps.billing.services import generate_invoice, issue_invoice
from apps.billing.usage import BillingIntegrityError, record_provider_usage
from apps.providers.models import ProviderCheck, ProviderCheckStatus


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
        )
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    recorded = 0
    for pk in checks:
        _, created = record_provider_usage(pk)
        recorded += int(created)
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
            status="active",
            plan__published=True,
            deleted_at__isnull=True,
            started_at__date__lt=today.replace(day=1),
        )
        .annotate(period_complete=Exists(completed_period))
        .filter(
            period_complete=False,
        )
        .order_by("pk")
        .values_list("pk", flat=True)[:limit]
    )
    completed = 0
    for subscription_id in list(subscriptions):
        # Match generate_invoice's subscription-first lock order. Generation
        # and issuance commit together; existing drafts can resume safely.
        with transaction.atomic():
            subscription = (
                BillingSubscription.objects.select_for_update(of=("self",))
                .select_related("tenant", "plan")
                .get(pk=subscription_id)
            )
            if (
                subscription.status != "active"
                or subscription.deleted_at
                or not subscription.plan.published
            ):
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
    return completed
