from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
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
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderType,
)
from apps.risk.models import RiskAssessment
from apps.tenants.models import Tenant
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationStatus,
)


class BiometricsTaskTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Kwame Mensah",
            email="kwame@example.com",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
            policy_snapshot_json={
                "face_match_threshold": 0.85,
                "manual_review_threshold": 0.65,
            },
        )
        self.identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processing",
        )
        self.document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=self.identity_document,
            side="front",
            storage_key="uploads/documents/doc_good",
            captured_at=timezone.now(),
        )
        self.selfie_capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/sel_good",
            capture_type="image",
            captured_at=timezone.now(),
        )
        self.session = self.verification.sessions.create(
            tenant=self.tenant,
            session_token_hash="placeholder",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.selfie_upload = Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            purpose=UploadPurpose.SELFIE_CAPTURE,
            storage_key=self.selfie_capture.storage_key,
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            status=UploadStatus.CONSUMED,
            expires_at=timezone.now() + timedelta(minutes=10),
            consumed_at=timezone.now(),
        )
        self.liveness_provider = Provider.objects.create(
            name="Internal Liveness Engine",
            code="internal-liveness-test",
            provider_type=ProviderType.LIVENESS,
        )
        self.face_provider = Provider.objects.create(
            name="Internal Face Match Engine",
            code="internal-face-match-test",
            provider_type=ProviderType.BIOMETRIC,
        )
        self.liveness_check = LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            provider_check_id="pck_liveness",
            liveness_type="passive",
            status="inconclusive",
            checked_at=timezone.now(),
        )
        self.face_match = FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=self.identity_document,
            document_capture=self.document_capture,
            provider_check_id="pck_face",
            status="inconclusive",
            matched_at=timezone.now(),
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=self.liveness_provider,
            check_type="liveness",
            status=ProviderCheckStatus.PENDING,
            public_id="pck_liveness",
            started_at=timezone.now(),
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=self.face_provider,
            check_type="face_match",
            status=ProviderCheckStatus.PENDING,
            public_id="pck_face",
            started_at=timezone.now(),
        )

    @patch("apps.biometrics.tasks.run_face_compare")
    @patch("apps.biometrics.tasks.run_liveness_check")
    def test_biometrics_task_updates_evidence_and_verifies_verification(
        self, mock_liveness, mock_face
    ):
        mock_liveness.return_value = {
            "status": "completed",
            "score": 0.94,
            "confidence_level": "high",
            "passed": True,
            "model_name": "mock-liveness",
            "model_version": "v1",
        }
        mock_face.return_value = {
            "status": "completed",
            "match_score": 0.96,
            "confidence_level": "high",
            "matched": True,
            "threshold_used": 0.85,
            "model_name": "mock-face-match",
            "model_version": "v1",
        }

        result = process_verification_biometrics_task(self.liveness_check.public_id)

        self.assertEqual(result, VerificationStatus.VERIFIED)
        self.verification.refresh_from_db()
        self.liveness_check.refresh_from_db()
        self.face_match.refresh_from_db()
        self.selfie_capture.refresh_from_db()
        self.selfie_upload.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.liveness_check.status, "passed")
        self.assertEqual(self.face_match.status, "matched")
        self.assertEqual(self.selfie_capture.status, "validated")
        self.assertEqual(self.selfie_upload.status, UploadStatus.PROMOTED)
        self.assertTrue(
            RiskAssessment.objects.filter(verification=self.verification).exists()
        )
        self.assertTrue(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )
        self.assertTrue(
            Notification.objects.filter(template_code="verification.verified").exists()
        )
        self.assertEqual(mock_liveness.call_args.kwargs["selfie_storage_bucket"], "")
        self.assertEqual(mock_face.call_args.kwargs["selfie_storage_bucket"], "")

    @patch("apps.biometrics.tasks.queue_verification_status_notifications")
    @patch("apps.biometrics.tasks.queue_webhook_events")
    @patch("apps.biometrics.tasks.run_liveness_check")
    def test_provider_failure_preserves_evidence_and_routes_to_manual_review(
        self, mock_liveness, mock_queue_webhooks, mock_queue_notifications
    ):
        mock_liveness.side_effect = RuntimeError("AI service unavailable")

        result = process_verification_biometrics_task(self.liveness_check.public_id)

        self.assertEqual(result, VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.verification.refresh_from_db()
        self.liveness_check.refresh_from_db()
        self.face_match.refresh_from_db()
        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(
            self.verification.status,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.assertIsNone(self.verification.completed_at)
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.ERROR)
        # Face matching was never attempted because liveness failed first.
        # Preserve its initial state instead of reporting a false provider error.
        self.assertEqual(self.face_match.status, FaceMatchStatus.INCONCLUSIVE)
        self.assertEqual(
            decision.reason_code,
            "biometric_provider_unavailable",
        )
        mock_queue_webhooks.assert_called_once_with(
            tenant=self.tenant,
            event_type="verification.manual_review_required",
            payload={
                "verification_id": self.verification.public_id,
                "external_reference": self.verification.external_reference,
                "status": VerificationStatus.MANUAL_REVIEW_REQUIRED,
                "reason_code": "biometric_provider_unavailable",
            },
        )
        mock_queue_notifications.assert_called_once_with(
            verification=self.verification,
            decision=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            risk_level="high",
        )

    @patch("apps.biometrics.tasks.ensure_verification_evidence_report")
    @patch("apps.biometrics.tasks.queue_verification_status_notifications")
    @patch("apps.biometrics.tasks.queue_webhook_events")
    @patch("apps.biometrics.tasks.promote_upload_to_media_by_storage_key")
    @patch("apps.biometrics.tasks.run_face_compare")
    @patch("apps.biometrics.tasks.run_liveness_check")
    def test_failed_liveness_emits_rejected_outcome(
        self,
        mock_liveness,
        mock_face,
        mock_promote,
        mock_queue_webhooks,
        mock_queue_notifications,
        mock_evidence_report,
    ):
        mock_liveness.return_value = {
            "status": "completed",
            "score": 0.12,
            "confidence_level": "high",
            "passed": False,
            "model_name": "mediapipe-liveness",
            "model_version": "v1",
        }
        mock_face.return_value = {
            "status": "completed",
            "match_score": 0.96,
            "confidence_level": "high",
            "matched": True,
            "threshold_used": 0.85,
            "model_name": "insightface",
            "model_version": "buffalo_l",
        }

        result = process_verification_biometrics_task(self.liveness_check.public_id)

        self.assertEqual(result, VerificationStatus.REJECTED)
        mock_queue_webhooks.assert_called_once_with(
            tenant=self.tenant,
            event_type="verification.rejected",
            payload={
                "verification_id": self.verification.public_id,
                "external_reference": self.verification.external_reference,
                "status": VerificationStatus.REJECTED,
            },
        )
        mock_queue_notifications.assert_called_once()
        mock_evidence_report.assert_called_once()

    @patch("apps.biometrics.tasks.queue_verification_status_notifications")
    @patch("apps.biometrics.tasks.queue_webhook_events")
    @patch("apps.biometrics.tasks.run_face_compare")
    @patch("apps.biometrics.tasks.run_liveness_check")
    def test_face_failure_preserves_completed_liveness(
        self,
        mock_liveness,
        mock_face,
        mock_queue_webhooks,
        mock_queue_notifications,
    ):
        mock_liveness.return_value = {
            "status": "completed",
            "score": 0.94,
            "confidence_level": "high",
            "passed": True,
            "model_name": "active-liveness",
            "model_version": "v1",
        }
        mock_face.side_effect = RuntimeError("face comparison unavailable")

        result = process_verification_biometrics_task(self.liveness_check.public_id)

        self.assertEqual(result, VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.liveness_check.refresh_from_db()
        self.face_match.refresh_from_db()
        liveness_provider_check = ProviderCheck.objects.get(public_id="pck_liveness")
        face_provider_check = ProviderCheck.objects.get(public_id="pck_face")
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.PASSED)
        self.assertEqual(self.face_match.status, FaceMatchStatus.ERROR)
        self.assertEqual(liveness_provider_check.status, ProviderCheckStatus.COMPLETED)
        self.assertEqual(face_provider_check.status, ProviderCheckStatus.FAILED)
        mock_queue_webhooks.assert_called_once()
        mock_queue_notifications.assert_called_once()
