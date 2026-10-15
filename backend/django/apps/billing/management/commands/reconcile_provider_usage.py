"""Reconcile a bounded production batch without touching prices or payments."""
from django.core.management.base import BaseCommand, CommandError

from apps.billing.usage import record_provider_usage
from apps.providers.models import ProviderCheck, ProviderCheckStatus
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Create idempotent UNRATED usage facts for one approved tenant; never charges anyone."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Tenant public ID")
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **opts):
        if not 1 <= opts["limit"] <= 1000:
            raise CommandError("limit must be between 1 and 1000")
        tenant = Tenant.objects.filter(public_id=opts["tenant"]).first()
        if tenant is None:
            raise CommandError("Unknown tenant")
        ids = list(
            ProviderCheck.objects.filter(
                tenant=tenant,
                verification__project__environment="production",
                status__in=(
                    ProviderCheckStatus.COMPLETED,
                    ProviderCheckStatus.FAILED,
                    ProviderCheckStatus.TIMEOUT,
                ),
                completed_at__isnull=False,
                billing_usage_event__isnull=True,
            )
            .order_by("pk")
            .values_list("pk", flat=True)[: opts["limit"]]
        )
        created = 0
        for pk in ids:
            _, added = record_provider_usage(pk)
            created += int(added)
        self.stdout.write(
            f"Production unrated usage reconciled: scanned={len(ids)} recorded={created}"
        )
