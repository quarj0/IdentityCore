from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from apps.verifications import test_processing_job_review_races as fixtures
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    VerificationStatus,
)
from apps.verifications.processing_jobs import (
    ProcessingJobOwnershipLost,
    complete_processing_job,
    exhaust_processing_job,
    lock_processing_job_for_finalization,
)


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class HistoricalProcessingLockRaceTests(TransactionTestCase):
    setUp = fixtures.ProcessingJobReviewRaceTests.setUp
    _verification = fixtures.ProcessingJobReviewRaceTests._verification
    _liveness = fixtures.ProcessingJobReviewRaceTests._liveness
    _job = fixtures.ProcessingJobReviewRaceTests._job

    def test_finalization_and_exhaustion_share_lock_order(self):
        for attempt in range(3):
            verification = self._verification()
            resource = self._liveness(verification, f"lock-order-{attempt}")
            job = self._job(
                verification,
                resource,
                status=ProcessingJobStatus.PROCESSING,
                attempt_count=3,
            )
            start = Barrier(2)

            def worker(finalize):
                close_old_connections()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '10s'")
                        cursor.execute("SET statement_timeout = '15s'")
                    owner = ProcessingJob.objects.get(pk=job.pk)
                    start.wait(timeout=10)
                    if finalize:
                        try:
                            with transaction.atomic():
                                lock_processing_job_for_finalization(owner)
                                complete_processing_job(owner)
                            return "completed"
                        except ProcessingJobOwnershipLost:
                            return "superseded"
                    exhaust_processing_job(owner)
                    return "exhaustion_checked"
                finally:
                    connection.close()

            with patch(
                "apps.webhooks.services.queue_webhook_events", return_value=[]
            ), patch(
                "apps.notifications.services.queue_verification_status_notifications"
            ), patch(
                "apps.verifications.evidence_commit.ensure_verification_evidence_report"
            ):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    first = pool.submit(worker, True)
                    second = pool.submit(worker, False)
                    outcomes = {first.result(timeout=25), second.result(timeout=25)}
            job.refresh_from_db()
            verification.refresh_from_db()
            self.assertIn(
                job.status,
                {ProcessingJobStatus.COMPLETED, ProcessingJobStatus.EXHAUSTED},
            )
            if job.status == ProcessingJobStatus.COMPLETED:
                self.assertIn("completed", outcomes)
                self.assertEqual(verification.status, VerificationStatus.PROCESSING)
            else:
                self.assertIn("superseded", outcomes)
                self.assertEqual(
                    verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
                )
