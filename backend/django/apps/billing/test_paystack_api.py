"""Paystack-only customer API and authenticated callback contracts."""

import hashlib
import hmac
import json
from unittest.mock import patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from apps.billing import test_commercial as fixtures
from apps.billing.services import BillingError, begin_checkout


@override_settings(
    BILLING_PAYMENTS_ENABLED=True, PAYSTACK_SECRET_KEY="synthetic-test-secret"
)
class PaystackAPITests(TestCase):
    setUp = fixtures.CommercialBillingTests.setUp
    usage = fixtures.CommercialBillingTests.usage
    invoice = fixtures.CommercialBillingTests.invoice
    verified = fixtures.CommercialBillingTests.verified

    def test_checkout_requires_manage_billing_and_rejects_client_amounts(self):
        from apps.access_control.models import (
            Permission,
            Role,
            RolePermission,
            UserRole,
        )

        invoice = self.invoice()
        client = APIClient()
        client.force_authenticate(self.user)
        path = f"/api/v1/billing/invoices/{invoice.public_id}/checkout"
        self.assertEqual(client.post(path, {}, format="json").status_code, 403)
        role = Role.objects.create(tenant=self.tenant, name="Finance", scope="tenant")
        RolePermission.objects.create(
            role=role,
            permission=Permission.objects.get_or_create(
                code="manage_billing", defaults={"name": "Manage billing"}
            )[0],
        )
        UserRole.objects.create(tenant=self.tenant, user=self.user, role=role)
        with patch(
            "apps.billing.paystack.initialize",
            return_value="https://checkout.paystack.com/pay/synthetic",
        ):
            response = client.post(path, {"provider": "paystack"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["provider"], "paystack")
        self.assertEqual(
            client.post(
                path, {"provider": "paystack", "amount_minor": 1}, format="json"
            ).status_code,
            400,
        )

    def test_callback_authenticates_raw_bytes_without_user_login(self):
        invoice = self.invoice()
        with patch(
            "apps.billing.paystack.initialize",
            return_value="https://checkout.paystack.com/pay/synthetic",
        ):
            payment = begin_checkout(invoice, billing_email=self.user.email)
        body = json.dumps(
            {"event": "charge.success", "data": {"reference": payment.reference}}
        ).encode()
        signature = hmac.new(b"synthetic-test-secret", body, hashlib.sha512).hexdigest()
        client = APIClient()
        path = "/api/v1/billing/paystack/webhook"
        self.assertEqual(
            client.post(path, data=body, content_type="application/json").status_code,
            400,
        )
        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertEqual(
                client.post(
                    path,
                    data=body,
                    content_type="application/json",
                    HTTP_X_PAYSTACK_SIGNATURE=signature,
                ).status_code,
                200,
            )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")
        from apps.billing.webhook_tasks import reconcile_billing_webhooks_task

        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertEqual(reconcile_billing_webhooks_task(), 1)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")

    def test_unsupported_payment_provider_cannot_initialize_checkout(self):
        invoice = self.invoice()
        with patch("apps.billing.paystack.initialize") as gateway, self.assertRaises(
            BillingError
        ):
            begin_checkout(
                invoice, billing_email=self.user.email, provider="unsupported"
            )
        gateway.assert_not_called()

    def test_paystack_never_converts_a_non_ghs_invoice(self):
        invoice = self.invoice()
        invoice.currency = "USD"
        invoice.save(update_fields=["currency"])
        with patch("apps.billing.paystack.initialize") as gateway, self.assertRaises(
            BillingError
        ):
            begin_checkout(invoice, billing_email=self.user.email)
        gateway.assert_not_called()

    def test_callback_acknowledges_before_independent_gateway_work(self):
        from apps.billing.models import BillingPayment

        invoice = self.invoice()
        payment = BillingPayment.objects.create(
            invoice=invoice,
            provider="paystack",
            reference="icAsyncAcceptance",
            amount_minor=invoice.amount_minor,
            currency=invoice.currency,
        )
        body = json.dumps(
            {"event": "charge.success", "data": {"reference": payment.reference}}
        ).encode()
        signature = hmac.new(b"synthetic-test-secret", body, hashlib.sha512).hexdigest()
        with patch(
            "apps.billing.paystack.verify", return_value=self.verified(payment)
        ) as gateway:
            response = APIClient().post(
                "/api/v1/billing/paystack/webhook",
                data=body,
                content_type="application/json",
                HTTP_X_PAYSTACK_SIGNATURE=signature,
            )
        self.assertEqual(response.status_code, 200)
        gateway.assert_not_called()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")
