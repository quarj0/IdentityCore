"""Operator verification without exporting sensitive audit payloads."""

from django.core.management.base import BaseCommand, CommandError

from apps.audit.services import verify_audit_chain
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Verify authenticated audit chains; exit nonzero on corruption."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--tenant", help="Tenant public identifier")
        group.add_argument("--platform", action="store_true")
        group.add_argument("--all", action="store_true")

    def handle(self, *args, **options):
        tenants = Tenant.objects.order_by("pk")
        if options["tenant"]:
            tenant = tenants.filter(public_id=options["tenant"]).first()
            if tenant is None:
                raise CommandError("Unknown tenant identifier.")
            scopes = [(tenant.pk, tenant.public_id)]
        elif options["platform"]:
            scopes = [(None, "platform")]
        else:
            scopes = [(None, "platform"), *tenants.values_list("pk", "public_id")]
        failures = 0
        for tenant_id, public_id in scopes:
            valid, first_failure = verify_audit_chain(tenant_id=tenant_id)
            if valid:
                self.stdout.write(f"{public_id}: valid")
            else:
                failures += 1
                self.stderr.write(f"{public_id}: invalid at {first_failure}")
        if failures:
            raise CommandError(f"Audit integrity failed for {failures} scope(s).")
