import hashlib
import hmac
import json
import time
from copy import deepcopy
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing import stripe
from apps.billing import test_commercial as fixtures
from apps.billing.exceptions import GatewayError
from apps.billing.models import (
    BillingInvoice,
    BillingMeter,
    BillingPayment,
    BillingPaymentEvent,
    BillingPlan,
    BillingRefund,
)
from apps.billing.services import (
    BillingError,
    begin_checkout,
    confirm_gateway_payment,
    receive_stripe_webhook,
    reconcile_gateway_refund,
    reconcile_gateway_dispute,
)


@override_settings(
    STRIPE_SECRET_KEY="sk_test_synthetic",
    STRIPE_WEBHOOK_SECRET="whsec_synthetic",
    BILLING_RETURN_URL="https://dashboard.example.test/billing/return",
    STRIPE_PAYMENT_CURRENCIES=("USD", "EUR", "GBP"),
)
class StripeAdapterTests(SimpleTestCase):
    def session(self):
        return {
            "id": "cs_test_Synthetic1",
            "url": "https://checkout.stripe.com/c/pay/cs_test_Synthetic1",
            "client_reference_id": "icSynthetic1",
            "mode": "payment",
            "amount_total": 10750,
            "currency": "usd",
            "status": "complete",
            "payment_status": "paid",
            "payment_intent": "pi_Synthetic1",
        }

    def intent(self):
        return {
            "id": "pi_Synthetic1",
            "amount": 10750,
            "amount_received": 10750,
            "currency": "usd",
            "status": "succeeded",
            "metadata": {"identitycore_payment_reference": "icSynthetic1"},
        }

    def initialize(self):
        return stripe.initialize(
            reference="icSynthetic1",
            email="synthetic@example.test",
            amount_minor=10750,
            currency="USD",
            payment_id="bpa_Synthetic1",
        )

    @patch("apps.billing.stripe._api")
    def test_checkout_sets_server_amount_currency_reference_and_idempotency(self, api):
        api.return_value = self.session()
        result = self.initialize()
        self.assertEqual(result["id"], "cs_test_Synthetic1")
        kwargs = api.call_args.kwargs
        self.assertEqual(kwargs["idempotency_key"], "icSynthetic1")
        self.assertEqual(
            kwargs["payload"]["line_items[0][price_data][unit_amount]"], 10750
        )
        self.assertEqual(
            kwargs["payload"]["line_items[0][price_data][currency]"], "usd"
        )
        self.assertEqual(kwargs["payload"]["mode"], "payment")
        self.assertIn("payment_id=bpa_Synthetic1", kwargs["payload"]["success_url"])
        self.assertNotIn("payment_method_types", kwargs["payload"])

    @patch("apps.billing.stripe._api")
    def test_checkout_refuses_wrong_host_protocol_credentials_port_and_attribution(
        self, api
    ):
        for changes in (
            {"url": "https://evil.example.test/checkout"},
            {"url": "http://checkout.stripe.com/pay"},
            {"url": "https://user@checkout.stripe.com/pay"},
            {"url": "https://checkout.stripe.com:444/pay"},
            {"url": "https://checkout.stripe.com:bad/pay"},
            {"amount_total": 1},
            {"amount_total": True},
            {"client_reference_id": "another"},
            {"mode": "subscription"},
            {"currency": "eur"},
        ):
            with self.subTest(changes=changes):
                api.return_value = {**self.session(), **changes}
                with self.assertRaises(GatewayError):
                    self.initialize()

    @patch("apps.billing.stripe._api")
    def test_payment_requires_independent_session_and_intent_confirmation(self, api):
        api.side_effect = [self.session(), self.intent()]
        result = stripe.verify(
            reference="icSynthetic1", checkout_id="cs_test_Synthetic1"
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["id"], "pi_Synthetic1")
        self.assertEqual(api.call_count, 2)

    @patch("apps.billing.stripe._api")
    def test_intent_attribution_mismatch_is_rejected(self, api):
        for changes in (
            {"id": "pi_Other"},
            {"amount": 1},
            {"amount": True},
            {"currency": "eur"},
            {"metadata": {"identitycore_payment_reference": "another"}},
        ):
            with self.subTest(changes=changes):
                api.side_effect = [self.session(), {**self.intent(), **changes}]
                with self.assertRaises(GatewayError):
                    stripe.verify(
                        reference="icSynthetic1", checkout_id="cs_test_Synthetic1"
                    )

    @patch("apps.billing.stripe._api")
    def test_unpaid_async_payment_is_not_settled(self, api):
        api.side_effect = [
            {**self.session(), "payment_status": "unpaid"},
            {**self.intent(), "status": "processing"},
        ]
        self.assertEqual(
            stripe.verify(reference="icSynthetic1", checkout_id="cs_test_Synthetic1")[
                "status"
            ],
            "pending",
        )

    @patch("apps.billing.stripe._api")
    def test_open_checkout_with_retryable_card_failure_stays_pending(self, api):
        api.side_effect = [
            {**self.session(), "status": "open", "payment_status": "unpaid"},
            {**self.intent(), "status": "requires_payment_method"},
        ]
        self.assertEqual(
            stripe.verify(reference="icSynthetic1", checkout_id="cs_test_Synthetic1")[
                "status"
            ],
            "pending",
        )

    @patch("apps.billing.stripe._api")
    def test_expired_session_is_terminal_without_intent_lookup(self, api):
        api.return_value = {
            **self.session(),
            "status": "expired",
            "payment_status": "unpaid",
            "payment_intent": None,
        }
        self.assertEqual(
            stripe.verify(reference="icSynthetic1", checkout_id="cs_test_Synthetic1")[
                "status"
            ],
            "failed",
        )
        api.assert_called_once()

    @patch("apps.billing.stripe._api")
    def test_incomplete_amount_received_never_settles(self, api):
        api.side_effect = [self.session(), {**self.intent(), "amount_received": 1}]
        self.assertEqual(
            stripe.verify(reference="icSynthetic1", checkout_id="cs_test_Synthetic1")[
                "status"
            ],
            "pending",
        )

    def test_invalid_resource_identifiers_never_reach_network(self):
        with patch("apps.billing.stripe._api") as api:
            for value in (
                "../payment_intents/pi_X",
                "https://evil.example",
                "cs_test_X?expand=all",
                None,
                1,
            ):
                with self.subTest(value=value), self.assertRaises(GatewayError):
                    stripe.verify(reference="icSynthetic1", checkout_id=value)
            api.assert_not_called()

    def test_signature_authenticates_raw_body_with_timestamp_tolerance_and_rotation(
        self,
    ):
        body = b'{"synthetic":true}'
        timestamp = 1700000000
        signature = hmac.new(
            b"whsec_synthetic", str(timestamp).encode() + b"." + body, hashlib.sha256
        ).hexdigest()
        header = f"t={timestamp},v1={'0'*64},v1={signature}"
        self.assertTrue(stripe.valid_webhook(body, header, now=timestamp))
        self.assertFalse(stripe.valid_webhook(body + b" ", header, now=timestamp))
        self.assertFalse(stripe.valid_webhook(body, header, now=timestamp + 301))
        self.assertFalse(stripe.valid_webhook(body, header, now=timestamp - 301))
        self.assertFalse(
            stripe.valid_webhook(body, header + f",t={timestamp}", now=timestamp)
        )
        self.assertFalse(stripe.valid_webhook(body, "t=bad,v1=bad", now=timestamp))

    @patch("apps.billing.stripe.request.build_opener")
    def test_wire_request_uses_fixed_endpoint_pinned_version_and_form_body(
        self, opener
    ):
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps(self.session()).encode()
        opener.return_value.open.return_value.__enter__.return_value = response
        self.initialize()
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(
            request.full_url, "https://api.stripe.com/v1/checkout/sessions"
        )
        self.assertEqual(request.get_header("Stripe-version"), stripe.API_VERSION)
        self.assertEqual(request.get_header("Idempotency-key"), "icSynthetic1")
        self.assertIn(
            b"line_items%5B0%5D%5Bprice_data%5D%5Bunit_amount%5D=10750", request.data
        )
        self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 8)


@override_settings(
    BILLING_PAYMENTS_ENABLED=True,
    BILLING_PAYMENT_PROVIDERS=("paystack", "stripe"),
    STRIPE_PAYMENT_CURRENCIES=("USD", "EUR", "GBP"),
    STRIPE_WEBHOOK_SECRET="whsec_synthetic",
    BILLING_RETURN_URL="https://dashboard.example.test/billing/return",
)
class StripePaymentFlowTests(TestCase):
    usage = fixtures.CommercialBillingTests.usage
    invoice = fixtures.CommercialBillingTests.invoice

    def setUp(self):
        fixtures.CommercialBillingTests.setUp(self)
        self.plan = BillingPlan.objects.create(
            code="stripe-test",
            name="Stripe plan",
            currency="USD",
            monthly_price_minor=10000,
        )
        for scope, price in (("platform", 500), ("tenant_owned", 250)):
            BillingMeter.objects.create(
                plan=self.plan,
                provider_scope=scope,
                capability="liveness",
                outcome="completed",
                unit_price_minor=price,
            )
        self.plan.published = True
        self.plan.save(update_fields=["published"])
        self.subscription.plan = self.plan
        self.subscription.save(update_fields=["plan"])

    def checkout(self):
        invoice = self.invoice()
        with patch(
            "apps.billing.stripe.initialize",
            return_value={
                "id": "cs_test_Synthetic1",
                "url": "https://checkout.stripe.com/c/pay/cs_test_Synthetic1",
            },
        ):
            payment = begin_checkout(
                invoice, billing_email=self.user.email, provider="stripe"
            )
        return invoice, payment

    def receipt(self, payment, **changes):
        return {
            "reference": payment.reference,
            "amount": payment.amount_minor,
            "currency": payment.currency,
            "status": "success",
            "id": "pi_Synthetic1",
            "checkout_id": payment.gateway_checkout_id,
            **changes,
        }

    def settle(self, payment):
        with patch("apps.billing.stripe.verify", return_value=self.receipt(payment)):
            return confirm_gateway_payment(payment.reference)

    def signed_event(
        self,
        payment,
        *,
        kind="checkout.session.completed",
        event_id="evt_Synthetic1",
        object_changes=None,
    ):
        obj = {
            "id": payment.gateway_checkout_id,
            "client_reference_id": payment.reference,
            "payment_status": "paid",
            **(object_changes or {}),
        }
        body = json.dumps(
            {"id": event_id, "type": kind, "data": {"object": obj}}
        ).encode()
        timestamp = str(int(time.time()))
        digest = hmac.new(
            b"whsec_synthetic", timestamp.encode() + b"." + body, hashlib.sha256
        ).hexdigest()
        return body, f"t={timestamp},v1={digest}"

    def test_checkout_persists_provider_session_and_exact_invoice_currency(self):
        invoice, payment = self.checkout()
        self.assertEqual(payment.provider, "stripe")
        self.assertEqual(payment.gateway_checkout_id, "cs_test_Synthetic1")
        self.assertEqual(payment.currency, invoice.currency)
        self.assertEqual(payment.amount_minor, invoice.amount_minor)

    def test_disabled_provider_cannot_initialize_checkout(self):
        invoice = self.invoice()
        with override_settings(BILLING_PAYMENT_PROVIDERS=("paystack",)), patch(
            "apps.billing.stripe.initialize"
        ) as gateway:
            with self.assertRaises(BillingError):
                begin_checkout(
                    invoice, billing_email=self.user.email, provider="stripe"
                )
            gateway.assert_not_called()

    def test_paystack_cannot_charge_a_usd_invoice(self):
        invoice = self.invoice()
        with patch("apps.billing.paystack.initialize") as gateway, self.assertRaises(
            BillingError
        ):
            begin_checkout(invoice, billing_email=self.user.email, provider="paystack")
        gateway.assert_not_called()

    def test_pending_checkout_blocks_second_gateway(self):
        invoice, payment = self.checkout()
        invoice.currency = "GHS"
        invoice.save(update_fields=["currency"])
        with patch("apps.billing.paystack.initialize") as gateway, self.assertRaises(
            BillingError
        ):
            begin_checkout(invoice, billing_email=self.user.email, provider="paystack")
        self.assertEqual(BillingPayment.objects.filter(invoice=invoice).count(), 1)
        gateway.assert_not_called()

    def test_duplicate_confirmation_does_not_settle_twice(self):
        invoice, payment = self.checkout()
        self.assertTrue(self.settle(payment))
        self.assertTrue(self.settle(payment))
        invoice.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
        self.assertEqual(payment.gateway_transaction_id, "pi_Synthetic1")

    def test_wrong_amount_currency_or_session_cannot_settle(self):
        invoice, payment = self.checkout()
        for changes in (
            {"amount": 1},
            {"amount": True},
            {"currency": "GHS"},
            {"checkout_id": "cs_test_Another"},
        ):
            with self.subTest(changes=changes), patch(
                "apps.billing.stripe.verify",
                return_value=self.receipt(payment, **changes),
            ), self.assertRaises(BillingError):
                confirm_gateway_payment(payment.reference)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")

    def test_signed_webhook_is_independently_verified_and_deduplicated(self):
        invoice, payment = self.checkout()
        body, signature = self.signed_event(payment)
        with patch(
            "apps.billing.stripe.verify", return_value=self.receipt(payment)
        ) as gateway:
            self.assertTrue(receive_stripe_webhook(body, signature))
            self.assertTrue(receive_stripe_webhook(body, signature))
            self.assertEqual(gateway.call_count, 2)
        self.assertEqual(BillingPaymentEvent.objects.count(), 1)
        event = BillingPaymentEvent.objects.get()
        self.assertEqual(event.provider, "stripe")
        self.assertEqual(event.gateway_event_id, "evt_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")

    def test_unpaid_async_webhook_cannot_settle(self):
        invoice, payment = self.checkout()
        body, signature = self.signed_event(payment)
        with patch(
            "apps.billing.stripe.verify",
            return_value=self.receipt(payment, status="pending", id=None),
        ):
            self.assertFalse(receive_stripe_webhook(body, signature))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "issued")
        self.assertEqual(BillingPaymentEvent.objects.count(), 0)

    def test_invalid_signature_rejected_before_provider_lookup(self):
        _, payment = self.checkout()
        body, _ = self.signed_event(payment)
        with patch("apps.billing.stripe.verify") as gateway, self.assertRaises(
            BillingError
        ):
            receive_stripe_webhook(body, "t=0,v1=" + "0" * 64)
        gateway.assert_not_called()

    def test_paystack_event_cannot_settle_stripe_payment(self):
        _, payment = self.checkout()
        with self.assertRaises(BillingError), patch(
            "apps.billing.stripe.verify"
        ) as gateway:
            confirm_gateway_payment(payment.reference, provider="paystack")
        gateway.assert_not_called()

    def test_webhook_before_checkout_url_persistence_repairs_session(self):
        invoice, payment = self.checkout()
        payment.gateway_checkout_id = ""
        payment.checkout_url = ""
        payment.save(update_fields=["gateway_checkout_id", "checkout_url"])
        body, signature = self.signed_event(
            payment, object_changes={"id": "cs_test_Synthetic1"}
        )
        with patch(
            "apps.billing.stripe.verify",
            return_value=self.receipt(payment, checkout_id="cs_test_Synthetic1"),
        ):
            self.assertTrue(receive_stripe_webhook(body, signature))
        payment.refresh_from_db()
        self.assertEqual(payment.gateway_checkout_id, "cs_test_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")

    def test_partial_and_full_refunds_are_verified_and_cannot_overcredit(self):
        invoice, payment = self.checkout()
        self.settle(payment)
        result = {
            "id": "re_Synthetic1",
            "payment_intent": "pi_Synthetic1",
            "currency": "usd",
            "amount": 500,
            "status": "succeeded",
        }
        with patch("apps.billing.stripe.verify_refund", return_value=result):
            reconcile_gateway_refund("stripe", "re_Synthetic1")
            reconcile_gateway_refund("stripe", "re_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "partially_refunded")
        self.assertEqual(BillingRefund.objects.count(), 1)
        with patch(
            "apps.billing.stripe.verify_refund",
            return_value={
                **result,
                "id": "re_Synthetic2",
                "amount": payment.amount_minor,
            },
        ):
            with self.assertRaises(BillingError):
                reconcile_gateway_refund("stripe", "re_Synthetic2")
        with patch(
            "apps.billing.stripe.verify_refund",
            return_value={
                **result,
                "id": "re_Synthetic2",
                "amount": payment.amount_minor - 500,
            },
        ):
            reconcile_gateway_refund("stripe", "re_Synthetic2")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "refunded")
        self.assertEqual(invoice.amount_minor, payment.amount_minor)

    def test_wrong_transaction_refund_cannot_change_invoice(self):
        invoice, payment = self.checkout()
        self.settle(payment)
        with patch(
            "apps.billing.stripe.verify_refund",
            return_value={
                "id": "re_Synthetic1",
                "payment_intent": "pi_Another",
                "currency": "usd",
                "amount": 500,
                "status": "succeeded",
            },
        ), self.assertRaises(BillingError):
            reconcile_gateway_refund("stripe", "re_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")

    def test_dispute_resolution_is_independently_verified_and_terminal(self):
        invoice, payment = self.checkout()
        self.settle(payment)
        result = {
            "id": "dp_Synthetic1",
            "payment_intent": "pi_Synthetic1",
            "amount": payment.amount_minor,
            "currency": "usd",
            "status": "needs_response",
        }
        with patch("apps.billing.stripe.verify_dispute", return_value=result):
            reconcile_gateway_dispute("stripe", "dp_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "disputed")
        with patch(
            "apps.billing.stripe.verify_dispute",
            return_value={**result, "status": "won"},
        ):
            reconcile_gateway_dispute("stripe", "dp_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
        with patch("apps.billing.stripe.verify_dispute", return_value=result):
            reconcile_gateway_dispute("stripe", "dp_Synthetic1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")

    def test_checkout_api_accepts_provider_and_rejects_client_amounts(self):
        from apps.access_control.models import (
            Permission,
            Role,
            RolePermission,
            UserRole,
        )

        role = Role.objects.create(tenant=self.tenant, name="Finance", scope="tenant")
        RolePermission.objects.create(
            role=role,
            permission=Permission.objects.get_or_create(
                code="manage_billing", defaults={"name": "Manage billing"}
            )[0],
        )
        UserRole.objects.create(tenant=self.tenant, user=self.user, role=role)
        invoice = self.invoice()
        client = APIClient()
        client.force_authenticate(self.user)
        path = f"/api/v1/billing/invoices/{invoice.public_id}/checkout"
        with patch(
            "apps.billing.stripe.initialize",
            return_value={
                "id": "cs_test_Synthetic1",
                "url": "https://checkout.stripe.com/c/pay/cs_test_Synthetic1",
            },
        ):
            response = client.post(path, {"provider": "stripe"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["provider"], "stripe")
        self.assertEqual(
            client.post(
                path, {"provider": "stripe", "amount_minor": 1}, format="json"
            ).status_code,
            400,
        )

    def test_stripe_callback_requires_raw_signature_and_does_not_require_user_login(
        self,
    ):
        invoice, payment = self.checkout()
        client = APIClient()
        body, signature = self.signed_event(payment)
        path = "/api/v1/billing/stripe/webhook"
        self.assertEqual(
            client.post(path, data=body, content_type="application/json").status_code,
            400,
        )
        with patch("apps.billing.stripe.verify", return_value=self.receipt(payment)):
            self.assertEqual(
                client.post(
                    path,
                    data=body,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=signature,
                ).status_code,
                200,
            )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")
