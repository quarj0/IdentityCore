from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.biometrics.models import LivenessCheck, LivenessCheckStatus, SelfieCapture
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
from apps.verifications.processing_jobs import recover_stale_processing_jobs


@override_settings(PROCESSING_JOB_LEASE_SECONDS=300, PROCESSING_JOB_MAX_ATTEMPTS=3)
class ProcessingJobEvidencePreservationTests(TestCase):
    @patch("apps.verifications.evidence_commit.ensure_verification_evidence_report")
    @patch("apps.notifications.services.queue_verification_status_notifications")
    @patch("apps.webhooks.services.queue_webhook_events", return_value=[])
    def test_retry_exhaustion_preserves_completed_liveness_evidence(
        self, _mock_webhooks, _mock_notifications, _mock_evidence
    ):
        organization = Organization.objects.create(
            name="Evidence Preservation", slug="evidence-preservation"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Evidence Preservation Tenant",
            slug="evidence-preservation-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant,
            full_name="Evidence Preservation Subject",
        )
        verification = Verification.objects.create(
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            purpose="Evidence preservation",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        selfie = SelfieCapture.objects.create(
            tenant=tenant,
            verification=verification,
            verification_subject=subject,
            storage_key="uploads/selfies/completed-before-exhaustion",
            capture_type="image",
            captured_at=timezone.now(),
        )
        liveness = LivenessCheck.objects.create(
            tenant=tenant,
            verification=verification,
            selfie_capture=selfie,
            liveness_type="passive",
            status=LivenessCheckStatus.PASSED,
            score="0.9800",
            checked_at=timezone.now(),
        )
        job = ProcessingJob.objects.create(
            tenant=tenant,
            verification=verification,
            job_type=ProcessingJobType.BIOMETRICS,
            resource_public_id=liveness.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

        with self.captureOnCommitCallbacks(execute=True):
            recovered, exhausted = recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        liveness.refresh_from_db()
        verification.refresh_from_db()
        self.assertEqual((recovered, exhausted), (0, 1))
        self.assertEqual(job.status, ProcessingJobStatus.EXHAUSTED)
        self.assertEqual(liveness.status, LivenessCheckStatus.PASSED)
        self.assertEqual(liveness.failure_reason, "")
        self.assertEqual(verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.assertEqual(
            verification.decision_record.reason_code, "processing_retries_exhausted"
        )
