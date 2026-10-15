"""Reconcile pending gateway transactions; no stored customer payment credentials."""
from django.core.management.base import BaseCommand, CommandError

from apps.billing import paystack
from apps.billing.models import BillingPayment
from apps.billing.services import BillingError, confirm_gateway_payment
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Verify pending Paystack references for a single tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--limit", default=50, type=int)

    def handle(self, **options):
        if not 1 <= options["limit"] <= 500:
            raise CommandError("Limit must be between 1 and 500")
        tenant = Tenant.objects.filter(public_id=options["tenant"]).first()
        if tenant is None:
            raise CommandError("Unknown tenant")
        references = list(
            BillingPayment.objects.filter(
                invoice__tenant=tenant, provider="paystack", status="pending"
            ).order_by("pk").values_list("reference", flat=True)[: options["limit"]]
        )
        settled = errors = 0
        for reference in references:
            try:
                if confirm_gateway_payment(reference):
                    settled += 1
            except (BillingError, paystack.GatewayError):
                errors += 1
        self.stdout.write(
            f"Payments checked={len(references)}, settled={settled}, "
            f"requires_attention={errors}"
        )
        if errors:
            raise CommandError("Payment reconciliation requires manual review")
