from django.core.management.base import BaseCommand, CommandError
from apps.tenants.models import Tenant
from common.tenant_storage import configure_route


class Command(BaseCommand):
    help = "Provision an immutable route to a deployment-approved bucket and region."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--environment", choices=["sandbox", "production"], required=True)
        parser.add_argument("--bucket", required=True)
        parser.add_argument("--residency-region", required=True)

    def handle(self, *args, **options):
        try:
            tenant = Tenant.objects.get(public_id=options["tenant"], deleted_at__isnull=True)
            route = configure_route(tenant, options["environment"], options["bucket"], options["residency_region"])
        except Exception:
            raise CommandError("Tenant storage route configuration failed.") from None
        self.stdout.write(f"route={route.public_id} environment={route.environment} residency_region={route.residency_region}")
