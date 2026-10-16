"""Durable callback acknowledgement and independently retriable reconciliation."""

import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import patch
from unittest import skipUnless
from django.db import connection, close_old_connections

from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing import test_commercial as fixtures
from apps.billing.exceptions import GatewayError
from apps.billing.models import BillingPayment, BillingWebhookEvent
from apps.billing.services import BillingError, enqueue_paystack_webhook
from apps.billing.webhook_tasks import (
    reconcile_billing_webhooks_task,
    reconcile_webhook,
)


@override_settings(PAYSTACK_SECRET_KEY="synthetic-test-secret")
class WebhookInboxTests(TestCase):
    setUp = fixtures.CommercialBillingTests.setUp
    usage = fixtures.CommercialBillingTests.usage
    invoice = fixtures.CommercialBillingTests.invoice
    verified = fixtures.CommercialBillingTests.verified

    def callback(self, event_type="charge.success", data=None):
        body = json.dumps(
            {"event": event_type, "data": data or {"reference": "icSyntheticInbox"}}
        ).encode()
        signature = hmac.new(b"synthetic-test-secret", body, hashlib.sha512).hexdigest()
        return body, signature

    def payment(self):
        invoice = self.invoice()
        return BillingPayment.objects.create(
            invoice=invoice,
            provider="paystack",
            reference="icSyntheticInbox",
            amount_minor=invoice.amount_minor,
            currency=invoice.currency,
        )

    def test_receipts_deduplicate_and_discard_customer_payload(self):
        body, signature = self.callback(
            data={
                "reference": "icSyntheticInbox",
                "customer": {"email": "private@example.test"},
                "authorization": {"card": "synthetic-private"},
            }
        )
        self.assertTrue(enqueue_paystack_webhook(body, signature))
        self.assertTrue(enqueue_paystack_webhook(body, signature))
        receipt = BillingWebhookEvent.objects.get()
        self.assertEqual(receipt.reference, "icSyntheticInbox")
        self.assertNotIn("private", str(receipt.__dict__))
        self.assertEqual(receipt.evidence_digest, hashlib.sha256(body).hexdigest())

    def test_invalid_signature_or_correlation_never_creates_receipt(self):
        body, signature = self.callback()
        with self.assertRaises(BillingError):
            enqueue_paystack_webhook(body, "0" * 128)
        for kind, data in [
            ("charge.success", {"reference": "bad/reference"}),
            ("refund.pending", {"transaction_reference": None, "id": True}),
            ("charge.dispute.create", {"id": -1}),
            ([], {}),
        ]:
            body, signature = self.callback(kind, data)
            with self.subTest(kind=kind), self.assertRaises(BillingError):
                enqueue_paystack_webhook(body, signature)
        self.assertFalse(BillingWebhookEvent.objects.exists())

    def test_gateway_outage_keeps_durable_receipt_for_retry(self):
        payment = self.payment()
        enqueue_paystack_webhook(*self.callback())
        with patch(
            "apps.billing.paystack.verify", side_effect=GatewayError("Synthetic outage")
        ), self.assertRaises(BillingError):
            reconcile_billing_webhooks_task()
        receipt = BillingWebhookEvent.objects.get()
        self.assertIsNone(receipt.processed_at)
        self.assertIsNone(receipt.lease_until)
        self.assertEqual(receipt.error_code, "gateway_reconciliation_failed")
        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertEqual(reconcile_billing_webhooks_task(), 1)
            self.assertEqual(reconcile_billing_webhooks_task(), 0)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "paid")

    def test_active_lease_skips_and_expired_lease_recovers(self):
        payment = self.payment()
        enqueue_paystack_webhook(*self.callback())
        receipt = BillingWebhookEvent.objects.get()
        receipt.lease_until = timezone.now() + timedelta(minutes=5)
        receipt.claim_token = "a" * 32
        receipt.save()
        with patch("apps.billing.paystack.verify") as gateway:
            self.assertEqual(reconcile_billing_webhooks_task(), 0)
            gateway.assert_not_called()
        receipt.lease_until = timezone.now() - timedelta(seconds=1)
        receipt.save()
        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertEqual(reconcile_billing_webhooks_task(), 1)

    def test_duplicate_http_delivery_acknowledges_during_gateway_work(self):
        payment = self.payment()
        body, signature = self.callback()
        enqueue_paystack_webhook(body, signature)

        def lookup(**kwargs):
            response = APIClient().post(
                "/api/v1/billing/paystack/webhook",
                data=body,
                content_type="application/json",
                HTTP_X_PAYSTACK_SIGNATURE=signature,
            )
            self.assertEqual(response.status_code, 200)
            return self.verified(payment)

        with patch("apps.billing.paystack.verify", side_effect=lookup):
            self.assertEqual(reconcile_billing_webhooks_task(), 1)
        self.assertEqual(BillingWebhookEvent.objects.count(), 1)

    def test_receipt_failure_does_not_starve_valid_later_receipt(self):
        payment = self.payment()
        bad = BillingWebhookEvent.objects.create(
            evidence_digest="a" * 64, event_type="charge.success", reference="icUnknown"
        )
        enqueue_paystack_webhook(*self.callback())

        def lookup(*, reference):
            if reference == "icUnknown":
                raise GatewayError("Synthetic outage")
            return self.verified(payment)

        with patch("apps.billing.paystack.verify", side_effect=lookup):
            with self.assertRaises(BillingError):
                reconcile_billing_webhooks_task(limit=1)
            self.assertEqual(reconcile_billing_webhooks_task(limit=1), 1)
        bad.refresh_from_db()
        self.assertIsNone(bad.processed_at)

    def test_lost_receipt_completion_replays_financial_commit_idempotently(self):
        payment = self.payment()
        enqueue_paystack_webhook(*self.callback())
        receipt = BillingWebhookEvent.objects.get()
        from apps.audit.models import AuditEvent

        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertTrue(reconcile_webhook(receipt.pk))
            BillingWebhookEvent.objects.filter(pk=receipt.pk).update(processed_at=None)
            self.assertTrue(reconcile_webhook(receipt.pk))
        self.assertEqual(
            AuditEvent.objects.filter(
                tenant=self.tenant, action="billing.payment.confirmed"
            ).count(),
            1,
        )

    def test_refund_http_callback_does_not_fetch_paginated_gateway_results(self):
        body, signature = self.callback(
            "refund.processed",
            {"transaction_reference": "icSyntheticInbox", "refund_reference": None},
        )
        with patch("apps.billing.paystack.list_refunds") as gateway:
            response = APIClient().post(
                "/api/v1/billing/paystack/webhook",
                data=body,
                content_type="application/json",
                HTTP_X_PAYSTACK_SIGNATURE=signature,
            )
            self.assertEqual(response.status_code, 200)
            gateway.assert_not_called()
        receipt = BillingWebhookEvent.objects.get()
        self.assertEqual(receipt.reference, "icSyntheticInbox")
        self.assertIsNone(receipt.resource_id)

    def test_soft_timeout_releases_lease_for_durable_retry(self):
        from celery.exceptions import SoftTimeLimitExceeded

        payment = self.payment()
        enqueue_paystack_webhook(*self.callback())
        with patch(
            "apps.billing.paystack.verify", side_effect=SoftTimeLimitExceeded()
        ), self.assertRaises(SoftTimeLimitExceeded):
            reconcile_billing_webhooks_task()
        receipt = BillingWebhookEvent.objects.get()
        self.assertIsNone(receipt.lease_until)
        self.assertIsNone(receipt.processed_at)
        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertEqual(reconcile_billing_webhooks_task(), 1)

    def test_terminal_gateway_failures_complete_receipts_without_confirming_payment(
        self,
    ):
        from apps.billing.services import confirm_gateway_payment

        payment = self.payment()
        for state in ("failed", "abandoned", "reversed"):
            enqueue_paystack_webhook(
                *self.callback(data={"reference": payment.reference, "marker": state})
            )
            result = self.verified(payment)
            result["status"] = state
            with patch("apps.billing.paystack.verify", return_value=result):
                self.assertEqual(reconcile_billing_webhooks_task(), 1)
                self.assertFalse(confirm_gateway_payment(payment.reference))
            payment.refresh_from_db()
            payment.invoice.refresh_from_db()
            self.assertEqual(payment.status, "failed")
            self.assertEqual(payment.invoice.status, "issued")
        self.assertEqual(
            BillingWebhookEvent.objects.filter(processed_at__isnull=False).count(), 3
        )

    def test_delayed_terminal_failure_preserves_an_already_paid_invoice(self):
        from apps.billing.services import confirm_gateway_payment
        from apps.audit.models import AuditEvent

        payment = self.payment()
        with patch("apps.billing.paystack.verify", return_value=self.verified(payment)):
            self.assertTrue(confirm_gateway_payment(payment.reference))
        enqueue_paystack_webhook(*self.callback())
        result = self.verified(payment)
        result["status"] = "reversed"
        with patch("apps.billing.paystack.verify", return_value=result):
            self.assertEqual(reconcile_billing_webhooks_task(), 1)
        payment.refresh_from_db()
        payment.invoice.refresh_from_db()
        self.assertEqual(payment.status, "paid")
        self.assertEqual(payment.invoice.status, "paid")
        self.assertEqual(
            AuditEvent.objects.filter(
                tenant=self.tenant, action="billing.payment.confirmed"
            ).count(),
            1,
        )

    def test_worker_is_registered_through_default_task_discovery(self):
        from apps.billing import tasks

        self.assertIs(
            tasks.reconcile_billing_webhooks_task, reconcile_billing_webhooks_task
        )


@skipUnless(connection.vendor == "postgresql", "Real PostgreSQL row locks required")
@override_settings(PAYSTACK_SECRET_KEY="synthetic-test-secret")
class WebhookLeaseRaceTests(TransactionTestCase):
    setUp = fixtures.CommercialBillingTests.setUp
    usage = fixtures.CommercialBillingTests.usage
    invoice = fixtures.CommercialBillingTests.invoice
    verified = fixtures.CommercialBillingTests.verified
    callback = WebhookInboxTests.callback
    payment = WebhookInboxTests.payment

    def test_network_work_does_not_hold_inbox_lock_or_duplicate_claim(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        import time

        payment = self.payment()
        body, signature = self.callback()
        enqueue_paystack_webhook(body, signature)
        receipt = BillingWebhookEvent.objects.get()
        entered, release = Event(), Event()

        def lookup(**kwargs):
            entered.set()
            if not release.wait(15):
                raise AssertionError(
                    "Concurrent receipt claim blocked behind network work"
                )
            return self.verified(payment)

        def worker():
            close_old_connections()
            try:
                return reconcile_webhook(receipt.pk)
            finally:
                close_old_connections()

        with patch(
            "apps.billing.paystack.verify", side_effect=lookup
        ) as gateway, ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(worker)
            try:
                self.assertTrue(entered.wait(10))
                started = time.monotonic()
                self.assertIsNone(reconcile_webhook(receipt.pk))
                response = APIClient().post(
                    "/api/v1/billing/paystack/webhook",
                    data=body,
                    content_type="application/json",
                    HTTP_X_PAYSTACK_SIGNATURE=signature,
                )
                self.assertEqual(response.status_code, 200)
                self.assertLess(time.monotonic() - started, 3)
            finally:
                release.set()
            self.assertTrue(future.result(timeout=10))
            self.assertEqual(gateway.call_count, 1)
        from apps.audit.models import AuditEvent

        self.assertEqual(
            AuditEvent.objects.filter(
                tenant=self.tenant, action="billing.payment.confirmed"
            ).count(),
            1,
        )
