from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import FaceMatch, LivenessCheck, SelfieCapture
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
        self.assertEqual(self.verification.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.liveness_check.status, "passed")
        self.assertEqual(self.face_match.status, "matched")
        self.assertTrue(
            RiskAssessment.objects.filter(verification=self.verification).exists()
        )
        self.assertTrue(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )
        self.assertTrue(
            Notification.objects.filter(template_code="verification.verified").exists()
        )
