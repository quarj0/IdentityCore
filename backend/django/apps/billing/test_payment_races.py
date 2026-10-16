import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.billing import test_commercial as fixtures
from apps.billing.models import (
    BillingDispute,
    BillingInvoice,
    BillingInvoiceLine,
    BillingPayment,
    BillingPaymentEvent,
    BillingRefund,
)
from apps.billing.services import (
    BillingError,
    begin_checkout,
    confirm_gateway_payment,
    issue_invoice,
    reconcile_gateway_dispute,
    reconcile_gateway_refund,
)


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
@override_settings(
    BILLING_PAYMENTS_ENABLED=True,
)
class PaymentRaceTests(TransactionTestCase):
    def setUp(self):
        fixtures.CommercialBillingTests.setUp(self)
        self.sequence = 0

    def new_invoice(self):
        self.sequence += 1
        invoice = BillingInvoice.objects.create(
            tenant=self.tenant,
            subscription=self.subscription,
            plan_code=self.plan.code,
            plan_version=self.plan.version,
            currency="GHS",
            period_start=date(2025, self.sequence, 1),
            period_end=date(2025, self.sequence + 1, 1),
            amount_minor=10750,
        )
        BillingInvoiceLine.objects.create(
            invoice=invoice,
            description="Synthetic issued invoice",
            quantity=1,
            unit_price_minor=10750,
            amount_minor=10750,
        )
        return issue_invoice(invoice.pk)

    def race(self, functions):
        start = Barrier(2)

        def worker(function):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET statement_timeout = '15s'")
                start.wait(timeout=10)
                return function()
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker, function) for function in functions]
            return [future.result(timeout=25) for future in futures]

    def test_overlapping_checkout_requests_initialize_one_payment(self):
        for round_number in range(3):
            invoice = self.new_invoice()

            def checkout():
                try:
                    return begin_checkout(
                        invoice, billing_email=self.user.email
                    ).public_id
                except BillingError:
                    return "blocked"

            with patch(
                "apps.billing.paystack.initialize",
                return_value="https://checkout.paystack.com/pay/synthetic",
            ) as gateway:
                results = self.race([checkout, checkout])
            self.assertEqual(gateway.call_count, 1)
            self.assertEqual(len(set(results) - {"blocked"}), 1)
            self.assertEqual(
                BillingPayment.objects.filter(
                    invoice=invoice, status="pending"
                ).count(),
                1,
            )

    def test_overlapping_confirmation_settles_and_audits_once(self):
        for round_number in range(3):
            invoice = self.new_invoice()
            payment = BillingPayment.objects.create(
                invoice=invoice,
                provider="paystack",
                reference=f"icPaystack{round_number}",
                amount_minor=invoice.amount_minor,
                currency="GHS",
            )
            receipt = {
                "reference": payment.reference,
                "amount": payment.amount_minor,
                "currency": "GHS",
                "status": "success",
                "id": 424200 + round_number,
            }
            digest = hashlib.sha256(payment.reference.encode()).hexdigest()

            def confirm():
                return confirm_gateway_payment(
                    payment.reference, evidence_digest=digest
                )

            with patch("apps.billing.paystack.verify", return_value=receipt):
                self.assertEqual(self.race([confirm, confirm]), [True, True])
            invoice.refresh_from_db()
            self.assertEqual(invoice.status, "paid")
            self.assertEqual(
                AuditEvent.objects.filter(
                    action="billing.payment.confirmed", target_id=payment.public_id
                ).count(),
                1,
            )
            self.assertEqual(
                BillingPaymentEvent.objects.filter(payment=payment).count(), 1
            )

    def test_refund_and_dispute_share_lock_order_and_preserve_both_records(self):
        for round_number in range(3):
            invoice = self.new_invoice()
            payment = BillingPayment.objects.create(
                invoice=invoice,
                provider="paystack",
                reference=f"icAdjust{round_number}",
                amount_minor=invoice.amount_minor,
                currency="GHS",
                status="paid",
                gateway_transaction_id=str(424500 + round_number),
                confirmed_at=timezone.now(),
            )
            invoice.status = "paid"
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=["status", "paid_at"])
            refund_id, dispute_id = (
                800 + round_number,
                900 + round_number,
            )
            with patch(
                "apps.billing.paystack.verify_refund",
                return_value={
                    "id": refund_id,
                    "transaction": int(payment.gateway_transaction_id),
                    "currency": "ghs",
                    "amount": 500,
                    "status": "processed",
                },
            ), patch(
                "apps.billing.paystack.verify_dispute",
                return_value={
                    "id": dispute_id,
                    "transaction": {
                        "id": int(payment.gateway_transaction_id),
                        "currency": "GHS",
                        "amount": payment.amount_minor,
                    },
                    "refund_amount": None,
                    "status": "pending",
                },
            ):
                self.assertEqual(
                    self.race(
                        [
                            lambda: reconcile_gateway_refund("paystack", refund_id),
                            lambda: reconcile_gateway_dispute("paystack", dispute_id),
                        ]
                    ),
                    [True, True],
                )
            invoice.refresh_from_db()
            self.assertEqual(invoice.status, "disputed")
            self.assertEqual(
                BillingRefund.objects.filter(
                    payment=payment, status="completed"
                ).count(),
                1,
            )
            self.assertEqual(
                BillingDispute.objects.filter(payment=payment, status="open").count(), 1
            )
