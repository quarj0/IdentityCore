from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.biometrics.models import (
    FaceMatch,
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
    SelfieCapture,
)
from apps.biometrics.tasks import process_verification_biometrics_task
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument
from apps.organizations.models import Organization
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.providers.services import create_provider_check
from apps.tenants.models import Tenant
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
    Verification,
    VerificationDecision,
    VerificationStatus,
)
from apps.verifications.processing_jobs import recover_stale_processing_jobs


class BiometricFinalizationRecoveryTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Finalization Recovery", slug="finalization-recovery"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Finalization Recovery Tenant",
            slug="finalization-recovery-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Recovery Subject",
            email="recovery@example.com",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Biometric finalization recovery",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
            policy_snapshot_json={
                "face_match_threshold": 0.85,
                "manual_review_threshold": 0.65,
            },
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processing",
        )
        document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/finalization-recovery",
            captured_at=timezone.now(),
        )
        self.selfie_capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/finalization-recovery",
            capture_type="image",
            captured_at=timezone.now(),
        )
        session = self.verification.sessions.create(
            tenant=self.tenant,
            session_token_hash="finalization-recovery-token",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=session,
            purpose=UploadPurpose.SELFIE_CAPTURE,
            storage_key=self.selfie_capture.storage_key,
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            status=UploadStatus.CONSUMED,
            expires_at=timezone.now() + timedelta(minutes=10),
            consumed_at=timezone.now(),
        )
        liveness_provider_check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.PENDING,
        )
        face_provider_check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.FACE_MATCH,
            status=ProviderCheckStatus.PENDING,
        )
        self.liveness_check = LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            provider_check_id=liveness_provider_check.public_id,
            liveness_type="passive",
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=timezone.now(),
        )
        self.face_match = FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=identity_document,
            document_capture=document_capture,
            provider_check_id=face_provider_check.public_id,
            status=FaceMatchStatus.INCONCLUSIVE,
            matched_at=timezone.now(),
        )

    @patch("apps.biometrics.tasks.ensure_verification_evidence_report")
    @patch("apps.biometrics.tasks.queue_verification_status_notifications")
    @patch("apps.biometrics.tasks.queue_webhook_events")
    @patch("apps.biometrics.tasks.promote_upload_to_media_by_storage_key")
    @patch("apps.biometrics.tasks.run_face_compare")
    @patch("apps.biometrics.tasks.run_liveness_check")
    def test_retry_resumes_finalization_without_reinvoking_providers(
        self,
        mock_liveness,
        mock_face,
        _mock_promote,
        mock_queue_webhooks,
        _mock_queue_notifications,
        mock_evidence_report,
    ):
        mock_liveness.return_value = {
            "status": "completed",
            "score": 0.97,
            "confidence_level": "high",
            "passed": True,
            "model_name": "recovery-liveness",
            "model_version": "v1",
            "metrics": {
                "face_count": 1,
                "avg_detection_confidence": 0.98,
            },
        }
        mock_face.return_value = {
            "status": "completed",
            "match_score": 0.96,
            "confidence_level": "high",
            "matched": True,
            "threshold_used": 0.85,
            "model_name": "recovery-face",
            "model_version": "v1",
        }
        mock_queue_webhooks.side_effect = RuntimeError("outbox insert failed")

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with self.assertRaisesRegex(RuntimeError, "outbox insert failed"):
                process_verification_biometrics_task(self.liveness_check.public_id)

        self.verification.refresh_from_db()
        self.liveness_check.refresh_from_db()
        self.face_match.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.PROCESSING)
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.PASSED)
        self.assertEqual(self.face_match.status, FaceMatchStatus.MATCHED)
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )
        self.assertEqual(callbacks, [])
        mock_evidence_report.assert_not_called()

        job = ProcessingJob.objects.get(
            job_type=ProcessingJobType.BIOMETRICS,
            resource_public_id=self.liveness_check.public_id,
        )
        job.lease_expires_at = timezone.now() - timedelta(seconds=1)
        job.save(update_fields=["lease_expires_at", "updated_at"])
        mock_liveness.reset_mock()
        mock_face.reset_mock()
        mock_queue_webhooks.side_effect = None
        mock_queue_webhooks.return_value = []

        with self.captureOnCommitCallbacks(execute=True):
            result = process_verification_biometrics_task(self.liveness_check.public_id)

        self.verification.refresh_from_db()
        job.refresh_from_db()
        self.assertEqual(result, VerificationStatus.VERIFIED)
        self.assertEqual(self.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(job.status, ProcessingJobStatus.COMPLETED)
        self.assertTrue(
            VerificationDecision.objects.filter(
                verification=self.verification,
                decision=VerificationStatus.VERIFIED,
            ).exists()
        )
        mock_liveness.assert_not_called()
        mock_face.assert_not_called()
        mock_evidence_report.assert_called_once()


@override_settings(PROCESSING_JOB_MAX_ATTEMPTS=3)
class PartialBiometricRecoverySweepTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Partial Recovery Sweep", slug="partial-recovery-sweep"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Partial Recovery Sweep Tenant",
            slug="partial-recovery-sweep-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant,
            full_name="Sweep Subject",
        )
        self.verification = Verification.objects.create(
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            purpose="Partial biometric recovery sweep",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        selfie_capture = SelfieCapture.objects.create(
            tenant=tenant,
            verification=self.verification,
            verification_subject=subject,
            storage_key="uploads/selfies/partial-recovery-sweep",
            capture_type="image",
            captured_at=timezone.now(),
        )
        self.liveness_check = LivenessCheck.objects.create(
            tenant=tenant,
            verification=self.verification,
            selfie_capture=selfie_capture,
            liveness_type="passive",
            status=LivenessCheckStatus.PASSED,
            checked_at=timezone.now(),
        )
        self.job = ProcessingJob.objects.create(
            tenant=tenant,
            verification=self.verification,
            job_type=ProcessingJobType.BIOMETRICS,
            resource_public_id=self.liveness_check.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=1,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=5),
            lease_expires_at=timezone.now() - timedelta(minutes=1),
        )

    @patch("apps.biometrics.tasks.process_verification_biometrics_task.delay")
    def test_stale_partial_biometric_result_is_redispatched(self, mock_delay):
        recovered, exhausted = recover_stale_processing_jobs(limit=10)

        self.job.refresh_from_db()
        self.assertEqual((recovered, exhausted), (1, 0))
        self.assertEqual(self.job.status, ProcessingJobStatus.QUEUED)
        mock_delay.assert_called_once_with(self.liveness_check.public_id)
