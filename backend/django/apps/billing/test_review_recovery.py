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

    def settled_paystack_payment(self):
        from apps.billing.models import BillingPayment

        invoice = self.invoice()
        invoice.status = "paid"
        invoice.save(update_fields=["status"])
        payment = BillingPayment.objects.create(
            invoice=invoice,
            reference="ic-reviewed-dispute",
            provider="paystack",
            status="paid",
            amount_minor=invoice.amount_minor,
            currency="GHS",
            gateway_transaction_id="42424242",
        )
        return invoice, payment

    def dispute_result(self, payment, **changes):
        result = {
            "id": 731,
            "status": "pending",
            "resolution": None,
            "refund_amount": None,
            "transaction": {
                "id": 42424242,
                "amount": payment.amount_minor,
                "currency": "GHS",
            },
        }
        result.update(changes)
        return result

    def test_partial_paystack_dispute_stores_verified_refund_amount(self):
        from apps.billing.services import reconcile_gateway_dispute
        from apps.billing.models import BillingDispute

        invoice, payment = self.settled_paystack_payment()
        result = self.dispute_result(
            payment,
            status="resolved",
            resolution="merchant-accepted",
            refund_amount=500,
        )
        with patch("apps.billing.paystack.verify_dispute", return_value=result):
            reconcile_gateway_dispute("paystack", 731)
        dispute = BillingDispute.objects.get(payment=payment)
        self.assertEqual(dispute.amount_minor, 500)
        self.assertEqual(dispute.status, "lost")

    def test_paystack_pending_dispute_can_resolve_for_partial_amount(self):
        from apps.billing.services import reconcile_gateway_dispute
        from apps.billing.models import BillingDispute

        invoice, payment = self.settled_paystack_payment()
        result = self.dispute_result(payment)
        with patch("apps.billing.paystack.verify_dispute", return_value=result):
            reconcile_gateway_dispute("paystack", 731)
        result.update(
            status="resolved", resolution="merchant-accepted", refund_amount=500
        )
        with patch("apps.billing.paystack.verify_dispute", return_value=result):
            reconcile_gateway_dispute("paystack", 731)
        dispute = BillingDispute.objects.get(payment=payment)
        self.assertEqual((dispute.status, dispute.amount_minor), ("lost", 500))

    def test_declined_paystack_dispute_closes_and_restores_paid_invoice(self):
        from apps.billing.services import reconcile_gateway_dispute
        from apps.billing.models import BillingDispute

        invoice, payment = self.settled_paystack_payment()
        result = self.dispute_result(payment)
        with patch("apps.billing.paystack.verify_dispute", return_value=result):
            reconcile_gateway_dispute("paystack", 731)
        result.update(status="resolved", resolution="declined")
        with patch("apps.billing.paystack.verify_dispute", return_value=result):
            reconcile_gateway_dispute("paystack", 731)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
        self.assertEqual(BillingDispute.objects.get(payment=payment).status, "won")

    def test_declined_paystack_dispute_accepts_verified_zero_refund(self):
        from apps.billing.services import reconcile_gateway_dispute
        from apps.billing.models import BillingDispute

        invoice, payment = self.settled_paystack_payment()
        result = self.dispute_result(
            payment, status="resolved", resolution="declined", refund_amount=0
        )
        with patch("apps.billing.paystack.verify_dispute", return_value=result):
            reconcile_gateway_dispute("paystack", 731)
        self.assertEqual(BillingDispute.objects.get(payment=payment).status, "won")

    @override_settings(BILLING_AUTO_INVOICE_ENABLED=True)
    def test_bad_subscription_does_not_abort_later_tenant_invoices(self):
        from apps.billing.models import BillingSubscription, BillingMeter
        from apps.billing.services import BillingError
        from apps.billing.tasks import generate_closed_month_invoices_task
        from apps.tenants.models import Tenant
        from apps.organizations.models import Organization

        self.usage(self.provider)
        BillingMeter.objects.filter(plan=self.plan).delete()
        organization = Organization.objects.create(
            name="Healthy billing", slug="healthy-billing"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Healthy",
            slug="healthy-billing",
            status="active",
        )
        BillingSubscription.objects.create(
            tenant=tenant,
            plan=self.plan,
            status="active",
            started_at=self.subscription.started_at,
        )
        with self.assertRaises(BillingError):
            generate_closed_month_invoices_task()
        self.assertTrue(
            BillingInvoice.objects.filter(tenant=tenant, status="issued").exists()
        )
        self.assertFalse(BillingInvoice.objects.filter(tenant=self.tenant).exists())
