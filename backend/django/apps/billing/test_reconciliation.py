from django.test import TestCase

from apps.billing import tests as usage_fixtures
from apps.billing import test_commercial as commercial_fixtures
from apps.billing.models import BillingInvoice
from apps.billing.services import BillingError, generate_invoice
from apps.billing.usage import record_provider_usage


class UsageReconciliationTests(TestCase):
    setUp = usage_fixtures.UsageLedgerTests.setUp
    make_check = usage_fixtures.UsageLedgerTests.make_check

    def test_reconciling_rated_usage_preserves_immutable_facts_and_rating(self):
        check = self.make_check(self.production, self.platform_provider)
        event, _ = record_provider_usage(check.pk)
        event.rating_state = "rated"
        event.save(update_fields=["rating_state"])
        repeated, created = record_provider_usage(check.pk)
        self.assertFalse(created)
        self.assertEqual(repeated.pk, event.pk)
        self.assertEqual(repeated.rating_state, "rated")


class InvoiceReconciliationTests(TestCase):
    setUp = commercial_fixtures.CommercialBillingTests.setUp
    usage = commercial_fixtures.CommercialBillingTests.usage

    def test_month_close_rejects_provider_evidence_changed_after_usage_capture(self):
        event = self.usage(self.provider)
        event.provider_check.status = "failed"
        event.provider_check.save(update_fields=["status"])
        with self.assertRaises(BillingError):
            generate_invoice(self.tenant, self.month)
        self.assertFalse(BillingInvoice.objects.exists())
        event.refresh_from_db()
        self.assertEqual(event.rating_state, "unrated")


from unittest.mock import patch
from django.test import override_settings
from apps.billing.tasks import generate_closed_month_invoices_task


@override_settings(BILLING_AUTO_INVOICE_ENABLED=True)
class InvoiceTaskRecoveryTests(TestCase):
    setUp = commercial_fixtures.CommercialBillingTests.setUp
    usage = commercial_fixtures.CommercialBillingTests.usage
    invoice = commercial_fixtures.CommercialBillingTests.invoice

    def test_existing_monthly_draft_resumes_issuance(self):
        self.usage(self.provider)
        invoice = generate_invoice(self.tenant, self.month)
        generate_closed_month_invoices_task()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")

    def test_issuance_failure_does_not_commit_partial_generation(self):
        self.usage(self.provider)
        with patch(
            "apps.billing.tasks.issue_invoice",
            side_effect=RuntimeError("synthetic outbox failure"),
        ):
            with self.assertRaises(RuntimeError):
                generate_closed_month_invoices_task()
        self.assertFalse(BillingInvoice.objects.filter(tenant=self.tenant).exists())

    def test_bounded_batch_moves_past_already_issued_tenants(self):
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant
        from apps.billing.models import BillingSubscription

        self.invoice()
        organization = Organization.objects.create(
            name="Second billing tenant", slug="second-billing-tenant"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Second tenant",
            slug="second-billing-tenant",
            status="active",
        )
        BillingSubscription.objects.create(
            tenant=tenant,
            plan=self.plan,
            status="active",
            started_at=self.subscription.started_at,
        )
        generate_closed_month_invoices_task(limit=1)
        self.assertTrue(
            BillingInvoice.objects.filter(
                tenant=tenant, period_start=self.period_start, status="issued"
            ).exists()
        )


@override_settings(BILLING_USAGE_CAPTURE_ENABLED=True)
class ScheduledUsageRecoveryTests(TestCase):
    setUp = usage_fixtures.UsageLedgerTests.setUp
    make_check = usage_fixtures.UsageLedgerTests.make_check

    def test_bounded_usage_reconciliation_recovers_platform_and_byop_once(self):
        from apps.billing.tasks import reconcile_billing_usage_task
        from apps.billing.models import BillingUsageEvent

        self.make_check(self.production, self.platform_provider)
        self.make_check(self.production, self.byop_provider)
        self.make_check(self.sandbox, self.platform_provider)
        self.assertEqual(reconcile_billing_usage_task(limit=1), 1)
        self.assertEqual(reconcile_billing_usage_task(limit=1), 1)
        self.assertEqual(reconcile_billing_usage_task(limit=1), 0)
        self.assertEqual(
            set(BillingUsageEvent.objects.values_list("provider_scope", flat=True)),
            {"platform", "tenant_owned"},
        )
        self.assertEqual(
            set(BillingUsageEvent.objects.values_list("rating_state", flat=True)),
            {"unrated"},
        )
        self.assertFalse(BillingInvoice.objects.exists())

    @override_settings(BILLING_USAGE_CAPTURE_ENABLED=False)
    def test_disabled_scheduled_usage_capture_records_nothing(self):
        from apps.billing.tasks import reconcile_billing_usage_task
        from apps.billing.models import BillingUsageEvent

        self.make_check(self.production, self.platform_provider)
        self.assertEqual(reconcile_billing_usage_task(), 0)
        self.assertFalse(BillingUsageEvent.objects.exists())

    def invalid_check(self):
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant
        from apps.providers.models import Provider

        org = Organization.objects.create(
            name="Other usage owner", slug="other-usage-owner"
        )
        tenant = Tenant.objects.create(
            organization=org, name="Other", slug="other-usage-owner", status="active"
        )
        provider = Provider.objects.create(
            tenant=tenant,
            name="Foreign provider",
            code="foreign-usage-provider",
            provider_type="liveness",
        )
        return self.make_check(self.production, provider)

    def test_invalid_check_is_quarantined_without_blocking_valid_usage(self):
        from io import StringIO
        from django.core.management import call_command
        from apps.billing.tasks import reconcile_billing_usage_task
        from apps.billing.usage import BillingIntegrityError
        from apps.billing.models import BillingUsageEvent

        bad = self.invalid_check()
        good = self.make_check(self.production, self.byop_provider)
        with self.assertRaises(BillingIntegrityError):
            reconcile_billing_usage_task()
        self.assertTrue(BillingUsageEvent.objects.filter(provider_check=good).exists())
        self.assertFalse(BillingUsageEvent.objects.filter(provider_check=bad).exists())
        from apps.billing.models import BillingUsageReconciliationIssue

        self.assertTrue(
            BillingUsageReconciliationIssue.objects.filter(provider_check=bad).exists()
        )
        bad.provider = self.platform_provider
        bad.save(update_fields=["provider"])
        call_command(
            "reconcile_provider_usage", tenant=self.tenant.public_id, stdout=StringIO()
        )
        self.assertTrue(BillingUsageEvent.objects.filter(provider_check=bad).exists())
        self.assertFalse(
            BillingUsageReconciliationIssue.objects.filter(provider_check=bad).exists()
        )

    def test_full_invalid_usage_page_cannot_starve_later_checks(self):
        from apps.billing.tasks import reconcile_billing_usage_task
        from apps.billing.usage import BillingIntegrityError
        from apps.billing.models import BillingUsageEvent

        self.invalid_check()
        good = self.make_check(self.production, self.platform_provider)
        with self.assertRaises(BillingIntegrityError):
            reconcile_billing_usage_task(limit=1)
        self.assertEqual(reconcile_billing_usage_task(limit=1), 1)
        self.assertTrue(BillingUsageEvent.objects.filter(provider_check=good).exists())

    def test_operator_usage_command_finishes_valid_checks_before_reporting_errors(self):
        from io import StringIO
        from django.core.management import call_command, CommandError
        from apps.billing.models import BillingUsageEvent

        self.invalid_check()
        good = self.make_check(self.production, self.platform_provider)
        with self.assertRaises(CommandError):
            call_command(
                "reconcile_provider_usage",
                tenant=self.tenant.public_id,
                stdout=StringIO(),
            )
        self.assertTrue(BillingUsageEvent.objects.filter(provider_check=good).exists())
