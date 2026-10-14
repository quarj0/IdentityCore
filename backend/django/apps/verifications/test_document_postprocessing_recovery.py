from copy import deepcopy
from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.audit.services import record_audit_event
from apps.identity_documents import tasks as document_tasks
from apps.identity_documents import tests as document_fixtures
from apps.identity_documents.models import IdentityDocumentStatus
from apps.verifications import test_processing_jobs as job_fixtures
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
)
from apps.verifications.processing_jobs import (
    ProcessingJobOwnershipLost,
    acquire_processing_job,
    recover_stale_processing_jobs,
)


class WorkerStopped(BaseException):
    pass


class DocumentFinalizationCommitTests(TestCase):
    setUp = document_fixtures.IdentityDocumentTaskTests.setUp

    def test_crash_before_final_audit_does_not_commit_document_success(self):
        def crash_on_final_audit(**kwargs):
            if kwargs["action"] == "document.processed":
                self.provider_results = {
                    name: deepcopy(getattr(document_tasks, name).return_value)
                    for name in (
                        "run_document_quality",
                        "run_document_ocr",
                        "run_document_classification",
                    )
                }
                raise WorkerStopped()
            return record_audit_event(**kwargs)

        with patch(
            "apps.identity_documents.tasks.record_audit_event",
            side_effect=crash_on_final_audit,
        ):
            with self.assertRaises(WorkerStopped):
                document_fixtures.IdentityDocumentTaskTests.test_process_identity_document_task_marks_document_processed(
                    self
                )
        self.identity_document.refresh_from_db()
        self.assertEqual(
            self.identity_document.status, IdentityDocumentStatus.PROCESSING
        )
        self.assertEqual(
            ProcessingJob.objects.get(
                resource_public_id=self.identity_document.public_id
            ).status,
            ProcessingJobStatus.PROCESSING,
        )
        self.assertFalse(
            AuditEvent.objects.filter(action="document.processed").exists()
        )

    def test_retry_after_finalization_crash_finishes_promoted_document(self):
        self.test_crash_before_final_audit_does_not_commit_document_success()
        job = ProcessingJob.objects.get(
            resource_public_id=self.identity_document.public_id
        )
        ProcessingJob.objects.filter(pk=job.pk).update(
            lease_expires_at=timezone.now() - timedelta(minutes=5)
        )
        with patch(
            "apps.identity_documents.tasks.process_identity_document_task.delay"
        ) as publish:
            self.assertEqual(recover_stale_processing_jobs(), (1, 0))
            publish.assert_called_once_with(self.identity_document.public_id)
        with patch.multiple(
            document_tasks,
            **{
                name: Mock(return_value=result)
                for name, result in self.provider_results.items()
            },
        ):
            result = document_tasks.process_identity_document_task(
                self.identity_document.public_id
            )
        self.assertEqual(result, IdentityDocumentStatus.PROCESSED)
        job.refresh_from_db()
        self.verification.refresh_from_db()
        self.upload.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.COMPLETED)
        self.assertEqual(self.verification.status, "awaiting_selfie")
        self.assertEqual(self.upload.status, "promoted")
        self.assertEqual(
            AuditEvent.objects.filter(action="document.processed").count(), 1
        )

    def test_lost_owner_escapes_without_provider_failure_writes(self):
        original_status = self.verification.status
        with patch(
            "apps.identity_documents.tasks.heartbeat_processing_job",
            side_effect=ProcessingJobOwnershipLost("synthetic superseded lease"),
        ):
            with self.assertRaises(ProcessingJobOwnershipLost):
                document_fixtures.IdentityDocumentTaskTests.test_process_identity_document_task_marks_document_processed(
                    self
                )
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual(
            self.identity_document.status, IdentityDocumentStatus.PROCESSING
        )
        self.assertEqual(self.verification.status, original_status)
        self.assertFalse(
            AuditEvent.objects.filter(action="document.processing_failed").exists()
        )

    def test_missing_captures_cannot_be_failed_by_superseded_worker(self):
        self.identity_document.captures.all().delete()
        original_status = self.identity_document.status
        owner = acquire_processing_job(
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource=self.identity_document,
        )
        ProcessingJob.objects.filter(pk=owner.pk).update(
            lease_generation=owner.lease_generation + 1
        )
        with patch(
            "apps.identity_documents.tasks.acquire_processing_job", return_value=owner
        ):
            with self.assertRaises(ProcessingJobOwnershipLost):
                document_tasks.process_identity_document_task(
                    self.identity_document.public_id
                )
        self.identity_document.refresh_from_db()
        self.assertEqual(self.identity_document.status, original_status)

    def test_missing_capture_failure_rolls_back_if_completion_is_interrupted(self):
        self.identity_document.captures.all().delete()
        original_status = self.identity_document.status
        with patch(
            "apps.identity_documents.tasks.complete_processing_job",
            side_effect=WorkerStopped(),
        ):
            with self.assertRaises(WorkerStopped):
                document_tasks.process_identity_document_task(
                    self.identity_document.public_id
                )
        self.identity_document.refresh_from_db()
        self.assertEqual(self.identity_document.status, original_status)
        self.assertEqual(
            ProcessingJob.objects.get(
                resource_public_id=self.identity_document.public_id
            ).status,
            ProcessingJobStatus.PROCESSING,
        )

    def test_current_owner_can_commit_missing_capture_failure(self):
        self.identity_document.captures.all().delete()
        result = document_tasks.process_identity_document_task(
            self.identity_document.public_id
        )
        self.assertEqual(result, IdentityDocumentStatus.FAILED)
        self.identity_document.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.FAILED)
        self.assertEqual(
            ProcessingJob.objects.get(
                resource_public_id=self.identity_document.public_id
            ).status,
            ProcessingJobStatus.COMPLETED,
        )

    def test_success_commits_document_marker_and_job_completion(self):
        document_fixtures.IdentityDocumentTaskTests.test_process_identity_document_task_marks_document_processed(
            self
        )
        self.assertEqual(
            ProcessingJob.objects.get(
                resource_public_id=self.identity_document.public_id
            ).status,
            ProcessingJobStatus.COMPLETED,
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                action="document.processed",
                metadata_json__identity_document_id=self.identity_document.public_id,
            ).exists()
        )


class DocumentPostprocessingRecoveryTests(TestCase):
    setUp = job_fixtures.ProcessingJobRecoveryTests.setUp

    def stale_job(self):
        self.identity_document.status = IdentityDocumentStatus.PROCESSED
        self.identity_document.save(update_fields=["status", "updated_at"])
        return ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id=self.identity_document.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=1,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_document_status_alone_does_not_complete_missing_postprocessing(
        self, publish
    ):
        job = self.stale_job()
        self.assertEqual(recover_stale_processing_jobs(), (1, 0))
        job.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        publish.assert_called_once_with(self.identity_document.public_id)

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_another_document_marker_cannot_complete_this_job(self, publish):
        job = self.stale_job()
        record_audit_event(
            tenant=self.tenant,
            actor=self.subject,
            action="document.processed",
            target_type="verification",
            target_id=self.verification.public_id,
            metadata={"identity_document_id": "doc_other"},
        )
        self.assertEqual(recover_stale_processing_jobs(), (1, 0))
        job.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        publish.assert_called_once_with(self.identity_document.public_id)
