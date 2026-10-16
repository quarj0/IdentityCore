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

    @override_settings(PAYSTACK_SECRET_KEY="synthetic-refund-webhook-secret")
    def test_documented_refund_webhook_without_numeric_id_reconciles(self):
        import hashlib
        import hmac
        import json
        from apps.billing.services import receive_paystack_webhook
        from apps.billing.models import BillingRefund

        invoice, payment = self.settled_paystack_payment()
        body = json.dumps(
            {
                "event": "refund.processed",
                "data": {
                    "transaction_reference": payment.reference,
                    "refund_reference": None,
                    "amount": "500",
                    "currency": "GHS",
                    "status": "processed",
                },
            }
        ).encode()
        signature = hmac.new(
            b"synthetic-refund-webhook-secret", body, hashlib.sha512
        ).hexdigest()
        rows = [
            {
                "id": 810,
                "transaction": 42424242,
                "amount": 500,
                "currency": "GHS",
                "status": "processed",
            }
        ]
        with patch(
            "apps.billing.paystack.list_refunds", return_value=rows, create=True
        ) as lookup:
            self.assertTrue(receive_paystack_webhook(body, signature))
        lookup.assert_called_once_with(transaction_id=42424242)
        self.assertEqual(BillingRefund.objects.get(payment=payment).amount_minor, 500)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "partially_refunded")

    def test_paystack_needs_attention_remains_pending(self):
        from apps.billing.services import reconcile_gateway_refund
        from apps.billing.models import BillingRefund

        invoice, payment = self.settled_paystack_payment()
        result = {
            "id": 811,
            "transaction": 42424242,
            "amount": 500,
            "currency": "GHS",
            "status": "needs-attention",
        }
        with patch("apps.billing.paystack.verify_refund", return_value=result):
            reconcile_gateway_refund("paystack", 811)
        self.assertEqual(BillingRefund.objects.get(payment=payment).status, "pending")

    @override_settings(PAYSTACK_SECRET_KEY="synthetic-refund-webhook-secret")
    def test_needs_attention_webhook_is_recorded_from_verified_lookup(self):
        import hashlib
        import hmac
        import json
        from apps.billing.services import receive_paystack_webhook
        from apps.billing.models import BillingRefund

        invoice, payment = self.settled_paystack_payment()
        body = json.dumps(
            {
                "event": "refund.needs-attention",
                "data": {
                    "transaction_reference": payment.reference,
                    "refund_reference": None,
                },
            }
        ).encode()
        signature = hmac.new(
            b"synthetic-refund-webhook-secret", body, hashlib.sha512
        ).hexdigest()
        rows = [
            {
                "id": 812,
                "transaction": 42424242,
                "amount": 500,
                "currency": "GHS",
                "status": "needs-attention",
            }
        ]
        with patch(
            "apps.billing.paystack.list_refunds", return_value=rows, create=True
        ):
            self.assertTrue(receive_paystack_webhook(body, signature))
        self.assertEqual(BillingRefund.objects.get(payment=payment).status, "pending")

    @override_settings(BILLING_AUTO_INVOICE_ENABLED=True)
    def test_full_page_of_failed_subscriptions_does_not_starve_later_tenant(self):
        from apps.billing.models import BillingSubscription
        from apps.billing.services import BillingError
        from apps.billing.tasks import generate_closed_month_invoices_task
        from apps.tenants.models import Tenant
        from apps.organizations.models import Organization

        tenants = [self.tenant]
        for number in (2, 3):
            org = Organization.objects.create(
                name=f"Fair batch {number}", slug=f"fair-batch-{number}"
            )
            tenant = Tenant.objects.create(
                organization=org,
                name=f"Fair {number}",
                slug=f"fair-batch-{number}",
                status="active",
            )
            BillingSubscription.objects.create(
                tenant=tenant,
                plan=self.plan,
                status="active",
                started_at=self.subscription.started_at,
            )
            tenants.append(tenant)

        def generate(tenant, month):
            if tenant.pk in {t.pk for t in tenants[:2]}:
                raise BillingError("Synthetic tenant accounting issue")
            return generate_invoice(tenant, month)

        with patch("apps.billing.tasks.generate_invoice", side_effect=generate):
            for _ in range(2):
                with self.assertRaises(BillingError):
                    generate_closed_month_invoices_task(limit=1)
            self.assertEqual(generate_closed_month_invoices_task(limit=1), 1)
        self.assertTrue(
            BillingInvoice.objects.filter(tenant=tenants[2], status="issued").exists()
        )

    def test_paystack_refund_listing_is_paginated_and_scoped_to_transaction(self):
        from apps.billing import paystack

        with patch(
            "apps.billing.paystack._api", side_effect=[[{}] * 50, [{"id": 99}]]
        ) as api:
            rows = paystack.list_refunds(transaction_id=42424242)
        self.assertEqual(len(rows), 51)
        self.assertEqual(api.call_count, 2)
        for page, call in enumerate(api.call_args_list, 1):
            self.assertEqual(
                call.args,
                ("GET", f"/refund?transaction=42424242&perPage=50&page={page}"),
            )
            self.assertEqual(call.kwargs, {"list_response": True})

    @override_settings(PAYSTACK_SECRET_KEY="synthetic-refund-webhook-secret")
    def test_refund_listing_cannot_credit_another_transaction(self):
        import hashlib
        import hmac
        import json
        from apps.billing.models import BillingRefund
        from apps.billing.services import BillingError, receive_paystack_webhook

        invoice, payment = self.settled_paystack_payment()
        body = json.dumps(
            {
                "event": "refund.processed",
                "data": {
                    "transaction_reference": payment.reference,
                    "refund_reference": None,
                },
            }
        ).encode()
        signature = hmac.new(
            b"synthetic-refund-webhook-secret", body, hashlib.sha512
        ).hexdigest()
        rows = [
            {
                "id": 813,
                "transaction": 999,
                "amount": 500,
                "currency": "GHS",
                "status": "processed",
            }
        ]
        with patch(
            "apps.billing.paystack.list_refunds", return_value=rows
        ), self.assertRaises(BillingError):
            receive_paystack_webhook(body, signature)
        self.assertFalse(BillingRefund.objects.exists())

    @override_settings(PAYSTACK_SECRET_KEY="synthetic-refund-webhook-secret")
    def test_refund_listing_releases_failed_reservations_before_new_credit(self):
        import hashlib
        import hmac
        import json
        from apps.billing.models import BillingRefund
        from apps.billing.services import receive_paystack_webhook

        invoice, payment = self.settled_paystack_payment()
        BillingRefund.objects.create(
            payment=payment,
            gateway_refund_id="paystack:814",
            amount_minor=payment.amount_minor,
            status="pending",
        )
        body = json.dumps(
            {
                "event": "refund.processed",
                "data": {
                    "transaction_reference": payment.reference,
                    "refund_reference": None,
                },
            }
        ).encode()
        signature = hmac.new(
            b"synthetic-refund-webhook-secret", body, hashlib.sha512
        ).hexdigest()
        rows = [
            {
                "id": 815,
                "transaction": 42424242,
                "amount": payment.amount_minor,
                "currency": "GHS",
                "status": "processed",
            },
            {
                "id": 814,
                "transaction": 42424242,
                "amount": payment.amount_minor,
                "currency": "GHS",
                "status": "failed",
            },
        ]
        with patch("apps.billing.paystack.list_refunds", return_value=rows):
            self.assertTrue(receive_paystack_webhook(body, signature))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "refunded")

    @override_settings(PAYSTACK_SECRET_KEY="synthetic-refund-webhook-secret")
    def test_paystack_transport_accepts_authenticated_refund_list_response(self):
        import json
        from apps.billing import paystack

        rows = [
            {
                "id": 816,
                "transaction": 42424242,
                "amount": 500,
                "currency": "GHS",
                "status": "processed",
            }
        ]
        with patch("apps.billing.paystack.urllib.request.build_opener") as build:
            response = build.return_value.open.return_value.__enter__.return_value
            response.status = 200
            response.read.return_value = json.dumps(
                {"status": True, "data": rows}
            ).encode()
            self.assertEqual(paystack.list_refunds(transaction_id=42424242), rows)
        outbound = build.return_value.open.call_args.args[0]
        self.assertEqual(
            outbound.full_url,
            "https://api.paystack.co/refund?transaction=42424242&perPage=50&page=1",
        )
        self.assertEqual(outbound.get_method(), "GET")
        self.assertEqual(outbound.get_header("User-agent"), "IdentityCore/1.0")
        self.assertEqual(build.return_value.open.call_args.kwargs, {"timeout": 8})

    @override_settings(BILLING_PAYMENTS_ENABLED=True)
    def test_interrupted_paystack_initialization_rotates_expired_reference(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.billing.models import BillingPayment
        from apps.billing.exceptions import GatewayError

        invoice = self.invoice()
        with patch(
            "apps.billing.paystack.initialize",
            side_effect=[
                GatewayError("Synthetic timeout after acceptance"),
                "https://checkout.paystack.com/pay/recovered",
            ],
        ) as gateway:
            with self.assertRaises(GatewayError):
                begin_checkout(invoice, billing_email=self.user.email)
            orphan = BillingPayment.objects.get(invoice=invoice)
            BillingPayment.objects.filter(pk=orphan.pk).update(
                created_at=timezone.now() - timedelta(minutes=3)
            )
            recovered = begin_checkout(invoice, billing_email=self.user.email)
        self.assertNotEqual(recovered.reference, orphan.reference)
        self.assertEqual(gateway.call_count, 2)
        orphan.refresh_from_db()
        self.assertEqual(orphan.status, "failed")
        self.assertEqual(recovered.status, "pending")

    def payment_recovery_rotation(self, *, unavailable=False):
        from django.core.management.base import CommandError
        from apps.billing.exceptions import GatewayError
        from apps.billing.models import BillingPayment

        invoice = self.invoice()
        later_invoice = BillingInvoice.objects.create(
            tenant=self.tenant,
            subscription=self.subscription,
            plan_code=invoice.plan_code,
            plan_version=invoice.plan_version,
            currency=invoice.currency,
            period_start=(self.period_start - timedelta(days=1)).replace(day=1),
            period_end=self.period_start,
            amount_minor=invoice.amount_minor,
            status="issued",
        )
        first, later = [
            BillingPayment.objects.create(
                invoice=current,
                provider="paystack",
                reference=f"icRotation{number}",
                amount_minor=current.amount_minor,
                currency=current.currency,
            )
            for number, current in enumerate((invoice, later_invoice), start=1)
        ]

        def verify(*, reference):
            if reference == first.reference:
                if unavailable:
                    raise GatewayError("Synthetic provider outage")
                result = self.verified(first)
                result["status"] = "ongoing"
                return result
            return self.verified(later)

        with patch("apps.billing.paystack.verify", side_effect=verify):
            if unavailable:
                with self.assertRaises(CommandError):
                    call_command(
                        "reconcile_billing_payments",
                        tenant=self.tenant.public_id,
                        limit=1,
                        stdout=StringIO(),
                    )
            else:
                call_command(
                    "reconcile_billing_payments",
                    tenant=self.tenant.public_id,
                    limit=1,
                    stdout=StringIO(),
                )
            call_command(
                "reconcile_billing_payments",
                tenant=self.tenant.public_id,
                limit=1,
                stdout=StringIO(),
            )
        first.refresh_from_db()
        later.refresh_from_db()
        self.assertEqual(first.status, "pending")
        self.assertEqual(later.status, "paid")

    def test_payment_recovery_advances_past_full_nonterminal_page(self):
        self.payment_recovery_rotation()

    def test_payment_recovery_advances_past_full_unavailable_page(self):
        self.payment_recovery_rotation(unavailable=True)

    def test_adjustment_recovery_rotates_pending_refunds_and_open_disputes(self):
        from apps.billing.models import BillingPayment, BillingRefund, BillingDispute

        invoice = self.invoice()
        payment = BillingPayment.objects.create(
            invoice=invoice,
            provider="paystack",
            reference="icAdjustmentRotation",
            amount_minor=invoice.amount_minor,
            currency=invoice.currency,
            status="paid",
            gateway_transaction_id="42424242",
        )
        for model, field, status, service in [
            (BillingRefund, "gateway_refund_id", "pending", "reconcile_gateway_refund"),
            (BillingDispute, "gateway_dispute_id", "open", "reconcile_gateway_dispute"),
        ]:
            for identifier in (101, 102):
                model.objects.create(
                    payment=payment,
                    amount_minor=50,
                    status=status,
                    **{field: f"paystack:{identifier}"},
                )
        with patch(
            "apps.billing.management.commands.reconcile_billing_payments.reconcile_gateway_refund",
            return_value=True,
        ) as refunds, patch(
            "apps.billing.management.commands.reconcile_billing_payments.reconcile_gateway_dispute",
            return_value=True,
        ) as disputes:
            for _ in range(2):
                call_command(
                    "reconcile_billing_payments",
                    tenant=self.tenant.public_id,
                    limit=1,
                    include_adjustments=True,
                    stdout=StringIO(),
                )
        for reconciler in (refunds, disputes):
            self.assertEqual(
                [call.args for call in reconciler.call_args_list],
                [("paystack", 101), ("paystack", 102)],
            )
