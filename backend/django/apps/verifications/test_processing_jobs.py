from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
    Verification,
    VerificationStatus,
)
from apps.verifications.processing_jobs import (
    acquire_processing_job,
    complete_processing_job,
    queue_identity_document_processing,
    recover_stale_processing_jobs,
)


@override_settings(PROCESSING_JOB_LEASE_SECONDS=300, PROCESSING_JOB_MAX_ATTEMPTS=3)
class ProcessingJobRecoveryTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Recovery Organization", slug="recovery-organization"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Recovery Tenant",
            slug="recovery-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Recovery Subject",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Processing recovery test",
            status=VerificationStatus.AWAITING_DOCUMENT,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status=IdentityDocumentStatus.PROCESSING,
        )

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_queue_persists_job_before_dispatch(self, mock_delay):
        with self.captureOnCommitCallbacks(execute=True):
            job = queue_identity_document_processing(self.identity_document)

        job.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        self.assertEqual(job.attempt_count, 0)
        self.assertGreater(job.lease_expires_at, timezone.now())
        mock_delay.assert_called_once_with(self.identity_document.public_id)

    def test_active_lease_blocks_duplicate_execution_and_completion_is_terminal(self):
        first = acquire_processing_job(
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource=self.identity_document,
        )
        duplicate = acquire_processing_job(
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource=self.identity_document,
        )

        self.assertIsNotNone(first)
        self.assertIsNone(duplicate)
        first.refresh_from_db()
        self.assertEqual(first.attempt_count, 1)

        complete_processing_job(first)
        self.assertIsNone(
            acquire_processing_job(
                job_type=ProcessingJobType.IDENTITY_DOCUMENT,
                resource=self.identity_document,
            )
        )

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_stale_lease_is_redispatched_without_incrementing_attempt(self, mock_delay):
        job = ProcessingJob.objects.create(
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

        recovered, exhausted = recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        self.assertEqual((recovered, exhausted), (1, 0))
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        self.assertEqual(job.attempt_count, 1)
        self.assertGreater(job.lease_expires_at, timezone.now())
        mock_delay.assert_called_once_with(self.identity_document.public_id)

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_terminal_exhaustion_routes_to_manual_review_with_safe_audit(
        self, mock_delay
    ):
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id=self.identity_document.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

        recovered, exhausted = recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual((recovered, exhausted), (0, 1))
        self.assertEqual(job.status, ProcessingJobStatus.EXHAUSTED)
        self.assertEqual(job.error_code, "processing_retries_exhausted")
        self.assertEqual(
            self.identity_document.status,
            IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.assertEqual(
            self.verification.status,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.assertEqual(
            self.verification.decision_record.reason_code,
            "processing_retries_exhausted",
        )
        event = AuditEvent.objects.get(
            action="verification.processing_retries_exhausted"
        )
        self.assertEqual(
            set(event.metadata_json),
            {"processing_job_id", "processing_job_type", "attempt_count"},
        )
        self.assertEqual(event.sensitive_metadata_hash, "")
        mock_delay.assert_not_called()

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_recovery_marks_committed_result_complete_instead_of_reprocessing(
        self, mock_delay
    ):
        self.identity_document.status = IdentityDocumentStatus.PROCESSED
        self.identity_document.save(update_fields=["status", "updated_at"])
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id=self.identity_document.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

        recovered, exhausted = recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual((recovered, exhausted), (0, 0))
        self.assertEqual(job.status, ProcessingJobStatus.COMPLETED)
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_DOCUMENT)
        self.assertFalse(hasattr(self.verification, "decision_record"))
        mock_delay.assert_not_called()
