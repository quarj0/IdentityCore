"""Regression coverage for independently reviewed billing recovery boundaries."""

from datetime import datetime, timedelta, timezone
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.billing import test_commercial as fixtures
from apps.billing.models import BillingInvoice
from apps.billing.services import (
    begin_checkout,
    confirm_gateway_payment,
    generate_invoice,
)


class BillingReviewRecoveryTests(TestCase):
    setUp = fixtures.CommercialBillingTests.setUp
    usage = fixtures.CommercialBillingTests.usage
    invoice = fixtures.CommercialBillingTests.invoice
    verified = fixtures.CommercialBillingTests.verified

    def test_first_day_partial_subscription_has_no_base_fee(self):
        self.subscription.started_at = datetime.combine(
            self.period_start, datetime.min.time(), timezone.utc
        ) + timedelta(hours=12)
        self.subscription.save(update_fields=["started_at"])
        self.usage(self.provider)
        invoice = generate_invoice(self.tenant, self.month)
        self.assertEqual(invoice.amount_minor, 500)

    def test_subscription_at_exact_month_start_has_full_base_fee(self):
        self.subscription.started_at = datetime.combine(
            self.period_start, datetime.min.time(), timezone.utc
        )
        self.subscription.save(update_fields=["started_at"])
        self.usage(self.provider)
        self.assertEqual(generate_invoice(self.tenant, self.month).amount_minor, 10500)

    @override_settings(BILLING_PAYMENTS_ENABLED=True)
    @patch(
        "apps.billing.paystack.initialize",
        return_value="https://checkout.paystack.com/test",
    )
    def test_reversed_pending_attempt_allows_a_fresh_checkout(self, initialize):
        invoice = self.invoice()
        payment = begin_checkout(invoice, billing_email=self.user.email)
        result = self.verified(payment)
        result["status"] = "reversed"
        with patch("apps.billing.paystack.verify", return_value=result):
            self.assertFalse(confirm_gateway_payment(payment.reference))
        payment.refresh_from_db()
        self.assertEqual(payment.status, "failed")
        replacement = begin_checkout(invoice, billing_email=self.user.email)
        self.assertNotEqual(replacement.pk, payment.pk)
        self.assertEqual(initialize.call_count, 2)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")

    def test_operator_can_issue_a_previously_generated_draft(self):
        self.usage(self.provider)
        call_command(
            "issue_billing_invoices",
            tenant=self.tenant.public_id,
            month=self.month,
            stdout=StringIO(),
        )
        draft = BillingInvoice.objects.get(tenant=self.tenant)
        self.assertEqual(draft.status, "draft")
        call_command(
            "issue_billing_invoices",
            tenant=self.tenant.public_id,
            month=self.month,
            issue=True,
            stdout=StringIO(),
        )
        draft.refresh_from_db()
        self.assertEqual(draft.status, "issued")
        self.assertEqual(BillingInvoice.objects.filter(tenant=self.tenant).count(), 1)

    def test_operator_issuance_failure_rolls_back_new_draft(self):
        self.usage(self.provider)
        with patch(
            "apps.billing.management.commands.issue_billing_invoices.issue_invoice",
            side_effect=RuntimeError("synthetic failure"),
        ):
            with self.assertRaises(RuntimeError):
                call_command(
                    "issue_billing_invoices",
                    tenant=self.tenant.public_id,
                    month=self.month,
                    issue=True,
                    stdout=StringIO(),
                )
        self.assertFalse(BillingInvoice.objects.filter(tenant=self.tenant).exists())
