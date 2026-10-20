from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless

from django.db import connection, transaction
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.evidence import test_races as race_helpers
from apps.providers import test_operations as fixtures, operations
from apps.providers.adapters import ProviderContractError
from apps.providers.models import ProviderOperation
from apps.verification_subjects.services import request_subject_deletion
from apps.verifications.processing_jobs import ProcessingJobOwnershipLost


@skipUnless(
    connection.vendor == "postgresql", "Provider completion races require PostgreSQL"
)
class ProviderOperationRaceTests(TransactionTestCase):
    create = fixtures.ProviderOperationTests.create
    invoke = fixtures.ProviderOperationTests.invoke
    pending = fixtures.ProviderOperationTests.pending
    completed = fixtures.ProviderOperationTests.completed
    _test_atomic_only = fixtures.ProviderOperationTests._test_atomic_only
    worker = race_helpers.GovernedResourceRaceTests.worker
    assert_locked = race_helpers.GovernedResourceRaceTests.assert_locked

    def setUp(self):
        fixtures.ProviderOperationTests.setUp(self)

    def test_concurrent_identical_completion_records_one_transition_and_audit(self):
        record = self.pending()
        response = self.completed(record)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(
                    self.worker,
                    lambda: operations.accept_response(
                        record.public_id, response
                    ).status,
                )
                for _ in range(2)
            ]
            self.assertEqual(
                [future.result(timeout=15) for future in futures],
                ["completed", "completed"],
            )
        self.assertEqual(
            AuditEvent.objects.filter(
                action="provider.operation_completed", target_id=record.public_id
            ).count(),
            1,
        )

    def test_erasure_waits_for_completion_then_scrubs_result_and_rejects_late_retry(
        self,
    ):
        record = self.pending()
        response = self.completed(record)
        ready, release, attempting, pids = Event(), Event(), Event(), []

        def complete():
            with transaction.atomic():
                operations.accept_response(record.public_id, response)
                ready.set()
                if not release.wait(10):
                    raise AssertionError("Completion barrier timed out")

        with ThreadPoolExecutor(max_workers=2) as pool:
            completion = pool.submit(self.worker, complete)
            self.assertTrue(ready.wait(10))
            deletion = pool.submit(
                self.worker,
                lambda: request_subject_deletion(
                    subject=self.subject, actor=self.approver
                ),
                attempting,
                pids,
            )
            try:
                self.assertTrue(attempting.wait(10))
                self.assert_locked(deletion, pids[0])
            finally:
                release.set()
            completion.result(timeout=15)
            self.assertEqual(deletion.result(timeout=15)["status"], "completed")
        record.refresh_from_db()
        self.assertEqual(record.result_json, {})
        self.assertEqual(record.remote_action, "delete")
        with self.assertRaises(ProcessingJobOwnershipLost):
            operations.accept_response(record.public_id, response)

    def test_cancel_committed_first_rejects_waiting_completion(self):
        record = self.pending()
        response = self.completed(record)
        attempted, pids = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                client = APIClient()
                client.force_authenticate(self.approver)
                result = client.post(
                    f"/api/v1/providers/operations/{record.public_id}/cancel",
                    {"project_id": self.project.public_id, "reason": "owner_cancelled"},
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="cancel-before-complete",
                )
                self.assertEqual(result.status_code, 200, result.data)
                completion = pool.submit(
                    self.worker,
                    lambda: operations.accept_response(record.public_id, response),
                    attempted,
                    pids,
                )
                self.assertTrue(attempted.wait(10))
                self.assert_locked(completion, pids[0])
            with self.assertRaises(ProviderContractError):
                completion.result(timeout=15)
        self.assertEqual(
            ProviderOperation.objects.get(pk=record.pk).status, "cancelled"
        )
