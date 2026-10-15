"""Bounded billing reconciliation and gated month-close Celery tasks."""
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.billing.models import BillingSubscription
from apps.billing.services import BillingError, generate_invoice, issue_invoice
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
        ).order_by("pk").values_list("pk", flat=True)[:limit]
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
    # Subscription is unique by tenant. Missing eligible meter or provider
    # reconciliation is a hard failure for that tenant, not a silent zero bill.
    subscriptions = BillingSubscription.objects.filter(
        status="active", plan__published=True, deleted_at__isnull=True,
    ).select_related("tenant").order_by("pk")[:limit]
    completed = 0
    for subscription in subscriptions:
        from apps.billing.models import BillingInvoice
        if BillingInvoice.objects.filter(
            tenant=subscription.tenant,
            period_start=(today.replace(day=1) - timedelta(days=1)).replace(day=1),
        ).exists():
            continue
        try:
            invoice = generate_invoice(subscription.tenant, previous_month)
            issue_invoice(invoice.pk)
            completed += 1
        except BillingError:
            # Unpriced, missing, or disputed usage must be escalated to
            # operators before issue; never suppress it as a paid zero bill.
            raise
    return completed
