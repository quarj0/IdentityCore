"""PostgreSQL proofs for governed writes, disclosures and subject erasure."""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.audit.services import lock_audit_chain
from apps.claims import tests as fixtures
from apps.evidence.services import revoke_authorization
from apps.verification_subjects.services import request_subject_deletion


@skipUnless(
    connection.vendor == "postgresql", "Governed resource races need PostgreSQL"
)
class GovernedResourceRaceTests(TransactionTestCase):
    propose = fixtures.ClaimsTests.propose
    create_evidence = fixtures.ClaimsTests.create_evidence
    claim = fixtures.ClaimsTests.claim
    normalized = fixtures.ClaimsTests.normalized
    policy = fixtures.ClaimsTests.policy
    issue = fixtures.ClaimsTests.issue
    redeem = fixtures.ClaimsTests.redeem

    def setUp(self):
        fixtures.ClaimsTests.setUp(self)

    def worker(self, callback, ready=None, pid=None):
        close_old_connections()
        try:
            connection.ensure_connection()
            if pid is not None:
                pid.append(connection.connection.info.backend_pid)
            if ready is not None:
                ready.set()
            return callback()
        finally:
            close_old_connections()

    def assert_locked(self, future, pid):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not future.done():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", [pid]
                )
                result = cursor.fetchone()
            if result and result[0] == "Lock":
                return
            time.sleep(0.02)
        self.fail(
            "Competing transaction did not wait for the tenant serialization lock"
        )

    def test_claim_creation_committed_before_erasure_is_included_and_scrubbed(self):
        inserted, release, attempting = Event(), Event(), Event()
        from apps.claims import services

        original = services._audit

        def audit(record, actor, action, *args, **kwargs):
            result = original(record, actor, action, *args, **kwargs)
            if action == "claims.created":
                inserted.set()
                if not release.wait(10):
                    raise AssertionError("Creation barrier timed out")
            return result

        with patch.object(services, "_audit", side_effect=audit), ThreadPoolExecutor(
            max_workers=2
        ) as pool:
            creation = pool.submit(self.worker, self.normalized)
            self.assertTrue(inserted.wait(10))
            pids = []
            deletion = pool.submit(
                self.worker,
                lambda: request_subject_deletion(
                    subject=self.subject, actor=self.checker
                ),
                attempting,
                pids,
            )
            try:
                self.assertTrue(attempting.wait(10))
                self.assert_locked(deletion, pids[0])
            finally:
                release.set()
            claim = creation.result(timeout=15)
            self.assertEqual(deletion.result(timeout=15)["status"], "completed")
        claim.refresh_from_db()
        self.assertEqual(claim.status, "deleted")
        self.assertEqual(claim.value_json, {})

    def test_erasure_committed_first_prevents_waiting_creation(self):
        attempted, pids = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                lock_audit_chain(self.tenant.pk)
                request_subject_deletion(subject=self.subject, actor=self.checker)
                creation = pool.submit(self.worker, self.normalized, attempted, pids)
                self.assertTrue(attempted.wait(10))
                self.assert_locked(creation, pids[0])
            with self.assertRaises(NotFound):
                creation.result(timeout=15)

    def test_revocation_committed_first_denies_waiting_and_replayed_redemptions(self):
        disclosure, token = self.issue(self.normalized(), self.policy())
        # An idempotent retry is still subject to the current authorization state.
        self.redeem(disclosure, token)
        attempted, pids = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                revoke_authorization(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    authorization_id=self.authorization.public_id,
                    reason="source_ended",
                )
                redemption = pool.submit(
                    self.worker, lambda: self.redeem(disclosure, token), attempted, pids
                )
                self.assertTrue(attempted.wait(10))
                self.assert_locked(redemption, pids[0])
            with self.assertRaises(PermissionDenied):
                redemption.result(timeout=15)
        disclosure.refresh_from_db()
        self.assertEqual(disclosure.redemption_count, 1)
