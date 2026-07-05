from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import FaceMatch, FaceMatchStatus, LivenessCheck, LivenessCheckStatus, SelfieCapture
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.organizations.models import Organization
from apps.risk.models import RiskRecommendation
from apps.risk.services import run_verification_risk_and_decision
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class RiskDecisionTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(tenant=self.tenant, full_name="Kwame Mensah")
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
            status=IdentityDocumentStatus.PROCESSING,
        )
        self.document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=self.identity_document,
            side="front",
            storage_key="uploads/documents/front",
            captured_at=timezone.now(),
        )
        self.selfie_capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/sel",
            capture_type="image",
            captured_at=timezone.now(),
        )

    def test_inconclusive_evidence_routes_to_manual_review(self):
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            liveness_type="passive",
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=timezone.now(),
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=self.identity_document,
            document_capture=self.document_capture,
            status=FaceMatchStatus.INCONCLUSIVE,
            matched_at=timezone.now(),
        )

        risk_assessment, decision_record = run_verification_risk_and_decision(self.verification)

        self.assertEqual(risk_assessment.recommendation, RiskRecommendation.MANUAL_REVIEW)
        self.assertEqual(decision_record.decision, VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED)

    def test_strong_evidence_is_automatically_approved(self):
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            liveness_type="passive",
            status=LivenessCheckStatus.PASSED,
            score=Decimal("0.9700"),
            checked_at=timezone.now(),
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=self.identity_document,
            document_capture=self.document_capture,
            status=FaceMatchStatus.MATCHED,
            match_score=Decimal("0.9600"),
            matched_at=timezone.now(),
        )

        risk_assessment, decision_record = run_verification_risk_and_decision(self.verification)

        self.assertEqual(risk_assessment.risk_level, "low")
        self.assertEqual(decision_record.decision, VerificationStatus.VERIFIED)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.VERIFIED)
        self.assertIsNotNone(self.verification.completed_at)

    def test_failed_liveness_is_automatically_rejected(self):
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            liveness_type="passive",
            status=LivenessCheckStatus.FAILED,
            score=Decimal("0.1200"),
            checked_at=timezone.now(),
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=self.identity_document,
            document_capture=self.document_capture,
            status=FaceMatchStatus.MATCHED,
            match_score=Decimal("0.9200"),
            matched_at=timezone.now(),
        )

        _, decision_record = run_verification_risk_and_decision(self.verification)

        self.assertEqual(decision_record.decision, VerificationStatus.REJECTED)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.REJECTED)
