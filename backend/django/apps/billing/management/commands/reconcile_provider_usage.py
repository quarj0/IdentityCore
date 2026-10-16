"""Reconcile a bounded production batch without touching prices or payments."""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from apps.billing.usage import reconcile_provider_usage_checks
from apps.providers.models import ProviderCheck, ProviderCheckStatus
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Create idempotent UNRATED usage facts for one approved tenant; never charges anyone."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Tenant public ID")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--check", help="Retry one provider check public ID")

    def handle(self, *args, **opts):
        if not 1 <= opts["limit"] <= 1000:
            raise CommandError("limit must be between 1 and 1000")
        tenant = Tenant.objects.filter(public_id=opts["tenant"]).first()
        if tenant is None:
            raise CommandError("Unknown tenant")
        checks = ProviderCheck.objects.filter(
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
        if opts.get("check"):
            checks = checks.filter(public_id=opts["check"])
        ids = list(
            checks.order_by(
                F("billing_reconciliation_issue__last_failed_at").asc(nulls_first=True),
                "pk",
            ).values_list("pk", flat=True)[: opts["limit"]]
        )
        created, failed = reconcile_provider_usage_checks(ids)
        self.stdout.write(
            f"Production unrated usage reconciled: scanned={len(ids)} recorded={created} requires_review={failed}"
        )
        if failed:
            raise CommandError("Usage reconciliation requires operator review")
