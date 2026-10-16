"""Invoice a CLOSED calendar month for a single tenant, operator initiated only."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.billing.services import (
    BillingError,
    generate_or_resume_draft_invoice,
    issue_invoice,
)
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Generate and optionally issue an immutable tenant invoice. No automatic payment."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--month", required=True, help="Closed UTC month, YYYY-MM")
        parser.add_argument("--issue", action="store_true", default=False)

    def handle(self, **options):
        tenant = Tenant.objects.filter(public_id=options["tenant"]).first()
        if tenant is None:
            raise CommandError("Unknown tenant")
        try:
            with transaction.atomic():
                invoice = generate_or_resume_draft_invoice(tenant, options["month"])
                if options["issue"]:
                    invoice = issue_invoice(invoice.pk)
        except BillingError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            f"Invoice {invoice.public_id}: {invoice.status}, "
            f"{invoice.currency} {invoice.amount_minor} minor units"
        )
