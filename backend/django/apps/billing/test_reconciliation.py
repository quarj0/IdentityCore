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
