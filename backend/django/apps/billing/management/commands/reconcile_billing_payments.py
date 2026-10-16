"""Reconcile gateway transactions and optional financial adjustments for one tenant."""

from django.core.management.base import BaseCommand, CommandError

from apps.billing.exceptions import GatewayError
from apps.billing.models import BillingDispute, BillingPayment, BillingRefund
from apps.billing.services import (
    BillingError,
    confirm_gateway_payment,
    reconcile_gateway_dispute,
    reconcile_gateway_refund,
)
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Independently verify Paystack payments for a single tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--limit", default=50, type=int)
        parser.add_argument("--provider", choices=("paystack",))
        parser.add_argument("--include-adjustments", action="store_true")

    def handle(self, **options):
        if not 1 <= options["limit"] <= 500:
            raise CommandError("Limit must be between 1 and 500")
        tenant = Tenant.objects.filter(public_id=options["tenant"]).first()
        if tenant is None:
            raise CommandError("Unknown tenant")
        payments = BillingPayment.objects.filter(
            invoice__tenant=tenant, status="pending"
        )
        if options["provider"]:
            payments = payments.filter(provider=options["provider"])
        references = list(
            payments.order_by("pk").values_list("reference", flat=True)[
                : options["limit"]
            ]
        )
        settled = errors = adjustments = 0
        for reference in references:
            try:
                settled += int(confirm_gateway_payment(reference))
            except (BillingError, GatewayError):
                errors += 1
        if options["include_adjustments"]:
            for model, reconciler in (
                (BillingRefund, reconcile_gateway_refund),
                (BillingDispute, reconcile_gateway_dispute),
            ):
                rows = model.objects.filter(payment__invoice__tenant=tenant)
                rows = rows.filter(
                    status="pending" if model is BillingRefund else "open"
                )
                if options["provider"]:
                    rows = rows.filter(payment__provider=options["provider"])
                field = (
                    "gateway_refund_id"
                    if model is BillingRefund
                    else "gateway_dispute_id"
                )
                for row in rows.select_related("payment").order_by("pk")[
                    : options["limit"]
                ]:
                    try:
                        prefix, _, identifier = getattr(row, field).partition(":")
                        if prefix != row.payment.provider or not identifier:
                            raise BillingError(
                                "Adjustment provider attribution is missing"
                            )
                        if prefix == "paystack":
                            identifier = int(identifier)
                        adjustments += int(reconciler(prefix, identifier))
                    except (BillingError, GatewayError, ValueError):
                        errors += 1
        self.stdout.write(
            f"Payments checked={len(references)}, settled={settled}, adjustments={adjustments}, requires_attention={errors}"
        )
        if errors:
            raise CommandError("Payment reconciliation requires manual review")
