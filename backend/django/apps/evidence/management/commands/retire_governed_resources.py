import json

from django.core.management.base import BaseCommand, CommandError

from apps.evidence.lifecycle import retire_expired_resources
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Retire due evidence, claim and authorization payloads with legal holds enforced."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Exact tenant public ID")
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(public_id=options["tenant"]).first()
        if tenant is None:
            raise CommandError("Tenant not found.")
        try:
            counts = retire_expired_resources(
                tenant_id=tenant.pk, limit=options["limit"]
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            json.dumps(
                {"tenant_id": tenant.public_id, "retired": counts}, sort_keys=True
            )
        )
