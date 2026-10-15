import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone as utc
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient as HTTPClient

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.billing.models import (
    BillingInvoice, BillingMeter, BillingPayment, BillingPlan,
    BillingSubscription, BillingUsageEvent,
)
from apps.billing.services import (
    BillingError, begin_checkout, confirm_gateway_payment, generate_invoice,
    issue_invoice, receive_paystack_webhook,
)
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.providers.models import Provider, ProviderCheck
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification


class CommercialBillingTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Billing Example", slug="commercial-example")
        self.tenant = Tenant.objects.create(
            organization=self.org, name="Billing Example", slug="commercial-example", status="active"
        )
        self.user = PlatformUser.objects.create_user(
            email="billing-test@example.com", password="SyntheticPassword123!",
            tenant=self.tenant, status=PlatformUserStatus.ACTIVE,
        )
        self.project = Project.objects.create(
            tenant=self.tenant, name="Production", slug="production",
            created_by=self.user, environment="production",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Synthetic Applicant"
        )
        self.provider = Provider.objects.create(
            name="Managed Liveness", code="commercial-test-managed", provider_type="liveness"
        )
        self.byop = Provider.objects.create(
            tenant=self.tenant, name="Bring Your Own", code="commercial-test-byop",
            provider_type="liveness",
        )
        self.plan = BillingPlan.objects.create(
            code="commercial-test", version=1, name="Test Plan",
            currency="GHS", monthly_price_minor=10000, published=False
        )
        self.subscription = BillingSubscription.objects.create(
            tenant=self.tenant, plan=self.plan, status="active",
            started_at=timezone.now() - timedelta(days=65),
        )
        self.period_end = timezone.now().date().replace(day=1)
        if self.period_end.month == 1:
            self.period_start = self.period_end.replace(year=self.period_end.year-1, month=12)
        else:
            self.period_start = self.period_end.replace(month=self.period_end.month-1)
        self.month = self.period_start.strftime("%Y-%m")
        self.occurred = datetime.combine(
            self.period_start + timedelta(days=3), datetime.min.time(), utc.utc
        )
        for scope, price in (("platform", 500), ("tenant_owned", 250)):
            BillingMeter.objects.create(
                plan=self.plan, provider_scope=scope,
                capability="liveness", outcome="completed",
                unit_price_minor=price,
            )
        self.plan.published = True
        self.plan.save(update_fields=["published"])

    def usage(self, provider):
        verification = Verification.objects.create(
            tenant=self.tenant, organization=self.org,
            verification_subject=self.subject, project=self.project,
            purpose="Synthetic test", expires_at=timezone.now() + timedelta(hours=2),
        )
        check = ProviderCheck.objects.create(
            tenant=self.tenant, verification=verification, provider=provider,
            check_type="liveness", status="completed",
            started_at=self.occurred, completed_at=self.occurred,
        )
        return BillingUsageEvent.objects.create(
            tenant=self.tenant, project=self.project, provider_check=check,
            environment="production", capability="liveness",
            provider_scope="tenant_owned" if provider.tenant_id else "platform",
            outcome="completed", quantity=1, occurred_at=self.occurred,
        )

    def invoice(self):
        self.usage(self.provider)
        self.usage(self.byop)
        invoice = generate_invoice(self.tenant, self.month)
        return issue_invoice(invoice.pk)

    def verified(self, payment, amount=None):
        return {
            "reference": payment.reference, "amount": (
                amount if amount is not None else payment.amount_minor
            ), "currency": payment.currency, "status": "success", "id": 42424242
        }

    def test_closed_month_price_is_snapshotted_per_provider_scope(self):
        managed = self.usage(self.provider)
        byop = self.usage(self.byop)
        invoice = generate_invoice(self.tenant, self.month)
        self.assertEqual(invoice.amount_minor, 10750)
        self.assertEqual(invoice.lines.count(), 3)
        self.assertEqual(managed.invoice_line.unit_price_minor, 500)
        self.assertEqual(byop.invoice_line.unit_price_minor, 250)
        managed.refresh_from_db()
        self.assertEqual(managed.rating_state, "rated")
        with self.assertRaises(BillingError):
            generate_invoice(self.tenant, self.month)

    def test_unpriced_byop_cannot_silently_be_invoiced(self):
        BillingMeter.objects.filter(plan=self.plan, provider_scope="tenant_owned").delete()
        event = self.usage(self.byop)
        with self.assertRaises(BillingError):
            generate_invoice(self.tenant, self.month)
        self.assertFalse(BillingInvoice.objects.exists())
        event.refresh_from_db()
        self.assertEqual(event.rating_state, "unrated")

    def test_current_month_cannot_be_invoiced(self):
        with self.assertRaises(BillingError):
            generate_invoice(self.tenant, timezone.now().date().strftime("%Y-%m"))

    def test_invoice_issuing_requires_matching_lines(self):
        invoice = generate_invoice(self.tenant, self.month)
        invoice.amount_minor += 1
        invoice.save(update_fields=["amount_minor"])
        with self.assertRaises(BillingError):
            issue_invoice(invoice.pk)

    def test_no_checkout_without_feature_activation(self):
        invoice = self.invoice()
        with self.assertRaises(BillingError):
            begin_checkout(invoice, billing_email=self.user.email)

    @override_settings(BILLING_PAYMENTS_ENABLED=True)
    @patch("apps.billing.paystack.initialize", return_value="https://checkout.paystack.com/abc")
    def test_checkout_uses_server_amount_and_persists_reference(self, gateway):
        invoice = self.invoice()
        payment = begin_checkout(invoice, billing_email=self.user.email)
        self.assertEqual(payment.amount_minor, invoice.amount_minor)
        self.assertEqual(payment.invoice_id, invoice.pk)
        self.assertEqual(payment.currency, "GHS")
        self.assertEqual(payment.checkout_url, "https://checkout.paystack.com/abc")
        gateway.assert_called_once()
        self.assertEqual(gateway.call_args.kwargs["amount_minor"], invoice.amount_minor)

    @patch("apps.billing.paystack.verify")
    def test_verified_payment_is_idempotent_and_matches_invoice(self, gateway):
        invoice = self.invoice()
        payment = BillingPayment.objects.create(
            invoice=invoice, reference="ic-test-idempotent-123",
            amount_minor=invoice.amount_minor, currency=invoice.currency,
        )
        gateway.return_value = self.verified(payment)
        self.assertTrue(confirm_gateway_payment(payment.reference))
        self.assertTrue(confirm_gateway_payment(payment.reference))
        payment.refresh_from_db()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
        self.assertEqual(payment.status, "paid")
        self.assertIsNotNone(invoice.paid_at)

    @patch("apps.billing.paystack.verify")
    def test_wrong_amount_cannot_mark_invoice_paid(self, gateway):
        invoice = self.invoice()
        payment = BillingPayment.objects.create(
            invoice=invoice, reference="ic-test-wrong-amount",
            amount_minor=invoice.amount_minor, currency=invoice.currency,
        )
        gateway.return_value = self.verified(payment, amount=1)
        with self.assertRaises(BillingError):
            confirm_gateway_payment(payment.reference)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")

    @override_settings(PAYSTACK_SECRET_KEY="synthetic-secret")
    @patch("apps.billing.paystack.verify")
    def test_signature_required_and_replay_does_not_double_settle(self, gateway):
        invoice = self.invoice()
        payment = BillingPayment.objects.create(
            invoice=invoice, reference="ic-test-signed-callback",
            amount_minor=invoice.amount_minor, currency=invoice.currency,
        )
        body = json.dumps({
            "event": "charge.success", "data": {"reference": payment.reference}
        }).encode("utf-8")
        digest = hmac.new(b"synthetic-secret", body, hashlib.sha512).hexdigest()
        with self.assertRaises(BillingError):
            receive_paystack_webhook(body, "0" * 128)
        gateway.assert_not_called()
        gateway.return_value = self.verified(payment)
        self.assertTrue(receive_paystack_webhook(body, digest))
        self.assertTrue(receive_paystack_webhook(body, digest))
        self.assertEqual(payment.events.count(), 1)

    def test_cross_tenant_invoice_is_not_visible(self):
        invoice = self.invoice()
        other_org = Organization.objects.create(name="Other", slug="commercial-other")
        other_tenant = Tenant.objects.create(
            organization=other_org, name="Other", slug="commercial-other", status="active",
        )
        other = PlatformUser.objects.create_user(
            email="billing-other@example.com", password="SyntheticPassword123!",
            tenant=other_tenant, status=PlatformUserStatus.ACTIVE,
        )
        http = HTTPClient()
        http.force_authenticate(other)
        response = http.get("/api/v1/billing/invoices/" + invoice.public_id)
        self.assertEqual(response.status_code, 404)

    def test_checkout_requires_billing_permission(self):
        invoice = self.invoice()
        http = HTTPClient()
        http.force_authenticate(self.user)
        response = http.post("/api/v1/billing/invoices/" + invoice.public_id + "/checkout")
        self.assertEqual(response.status_code, 403)
