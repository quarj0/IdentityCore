from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from apps.risk import test_external
from apps.risk.services import run_verification_risk_and_decision
from apps.verifications.models import Verification


@skipUnless(connection.vendor == "postgresql", "External I/O races require PostgreSQL")
class ExternalRiskFinalizationTests(TransactionTestCase):
    setUp = test_external.ExternalRiskTests.setUp

    def test_slow_external_io_does_not_block_cancellation(self):
        started, release = Event(), Event()

        def slow_provider(**kwargs):
            self.assertFalse(connection.in_atomic_block)
            started.set()
            if not release.wait(10):
                raise RuntimeError("Synthetic synchronization timeout")
            return test_external.evidence(10)

        self.adapter.risk_check.side_effect = slow_provider

        def worker():
            close_old_connections()
            try:
                return run_verification_risk_and_decision(
                    Verification.objects.get(pk=self.verification.pk)
                )
            finally:
                close_old_connections()

        def cancel():
            close_old_connections()
            try:
                with transaction.atomic():
                    current = Verification.objects.select_for_update(no_key=True).get(
                        pk=self.verification.pk
                    )
                    current.status = "cancelled"
                    current.decision_revision += 1
                    current.save(
                        update_fields=["status", "decision_revision", "updated_at"]
                    )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(worker)
            try:
                self.assertTrue(started.wait(5))
                pool.submit(cancel).result(timeout=3)
            finally:
                release.set()
            _, decision = future.result(timeout=10)
        self.assertIsNone(decision)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "cancelled")
        self.assertTrue(
            self.verification.provider_checks.filter(
                provider=self.provider, status="completed"
            ).exists()
        )
