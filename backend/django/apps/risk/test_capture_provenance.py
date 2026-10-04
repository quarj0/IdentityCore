from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import (
    FaceMatch,
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
)
from apps.risk.models import RiskRecommendation
from apps.risk.services import evaluate_risk_assessment
from apps.risk import tests as risk_tests
from apps.uploads.models import Upload, UploadStatus
from apps.verifications.models import VerificationSession


class CaptureRiskTests(TestCase):
    setUp = risk_tests.RiskDecisionTests.setUp

    def test_invalid_retained_receipt_cannot_approve_strong_biometrics(self):
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            liveness_type="passive",
            status=LivenessCheckStatus.PASSED,
            checked_at=timezone.now(),
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=self.identity_document,
            document_capture=self.document_capture,
            status=FaceMatchStatus.MATCHED,
            match_score=Decimal("0.99"),
            matched_at=timezone.now(),
        )
        self.assertEqual(
            evaluate_risk_assessment(self.verification).recommendation,
            RiskRecommendation.APPROVE,
        )
        session = VerificationSession(
            tenant=self.tenant,
            verification=self.verification,
            expires_at=self.verification.expires_at,
        )
        session.set_session_token("synthetic-capture-session")
        session.save()
        Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=session,
            purpose="selfie_capture",
            mime_type="image/jpeg",
            file_size_bytes=100,
            storage_key="synthetic-invalid-receipt",
            status=UploadStatus.CONSUMED,
            consumed_at=timezone.now(),
            expires_at=self.verification.expires_at,
            checksum_sha256="a" * 64,
            capture_provenance_version=1,
            capture_receipt="invalid",
        )
        result = evaluate_risk_assessment(self.verification)
        self.assertEqual(result.recommendation, RiskRecommendation.MANUAL_REVIEW)
        self.assertEqual(result.signals_json["capture_provenance"]["invalid"], 1)
