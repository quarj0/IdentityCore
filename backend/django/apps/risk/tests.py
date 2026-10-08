from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import (
    FaceMatch,
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
    SelfieCapture,
)
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.organizations.models import Organization
from apps.risk.models import RiskRecommendation
from apps.risk.services import run_verification_risk_and_decision
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationStatus,
)


class RiskDecisionTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Kwame Mensah"
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

    def test_ocr_outage_reason_remains_a_review_gate(self):
        from apps.risk.services import _document_requires_manual_review

        for classification in (
            {"issues": ["document_ocr_unavailable"]},
            {
                "manual_review": {
                    "required": False,
                    "reason_codes": ["document_ocr_unavailable"],
                }
            },
        ):
            self.assertTrue(_document_requires_manual_review(classification))
        self.assertFalse(_document_requires_manual_review({"issues": []}))

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

        risk_assessment, decision_record = run_verification_risk_and_decision(
            self.verification
        )

        self.assertEqual(
            risk_assessment.recommendation, RiskRecommendation.MANUAL_REVIEW
        )
        self.assertEqual(
            decision_record.decision, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        self.verification.refresh_from_db()
        self.assertEqual(
            self.verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )

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

        risk_assessment, decision_record = run_verification_risk_and_decision(
            self.verification
        )

        self.assertEqual(risk_assessment.risk_level, "low")
        self.assertEqual(decision_record.decision, VerificationStatus.VERIFIED)
        self.assertEqual(decision_record.contract_version, "1")
        self.assertEqual(decision_record.reason_codes_json, ["risk_rules_approved"])
        self.assertIn("provider_checks", decision_record.input_snapshot_json)
        self.assertEqual(self.verification.status, VerificationStatus.VERIFIED)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.VERIFIED)
        self.assertIsNotNone(self.verification.completed_at)

    def test_document_review_signal_overrides_strong_biometrics(self):
        self.identity_document.extracted_data_json = {
            "document_classification": {
                "classification_status": "unknown",
                "workflow_action": "continue_with_review",
                "requires_manual_review": True,
                "manual_review": {
                    "required": True,
                    "reason_codes": ["document_type_not_determined"],
                },
            }
        }
        self.identity_document.save(update_fields=["extracted_data_json", "updated_at"])
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

        risk_assessment, decision_record = run_verification_risk_and_decision(
            self.verification
        )

        self.assertEqual(
            risk_assessment.recommendation, RiskRecommendation.MANUAL_REVIEW
        )
        self.assertTrue(risk_assessment.signals_json["document_requires_manual_review"])
        self.assertEqual(
            decision_record.decision, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        self.verification.refresh_from_db()
        self.assertEqual(
            self.verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )

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

    def test_terminal_race_rejects_automatic_write_and_audits_conflict(self):
        Verification.objects.filter(pk=self.verification.pk).update(
            status=VerificationStatus.CANCELLED,
            cancelled_at=timezone.now(),
            completed_at=timezone.now(),
        )

        assessment, decision = run_verification_risk_and_decision(self.verification)
        self.assertIsNone(assessment)
        self.assertIsNone(decision)
        from apps.audit.models import AuditEvent

        self.assertTrue(
            AuditEvent.objects.filter(
                action="verification.automatic_decision_conflict"
            ).exists()
        )

        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )

    def test_stale_revision_cannot_replace_automatic_review_routing(self):
        from apps.audit.models import AuditEvent
        from apps.verifications.models import VerificationDecisionType
        from apps.risk.services import apply_automatic_decision
        from apps.risk.models import RiskAssessment

        decision = VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            decision="manual_review_required",
            decision_type=VerificationDecisionType.AUTOMATIC,
            reason_code="prior_route",
            decided_at=timezone.now(),
        )
        Verification.objects.filter(pk=self.verification.pk).update(
            decision_revision=1, status="manual_review_required"
        )
        assessment = RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            risk_score=14,
            risk_level="low",
            recommendation="approve",
        )
        result = apply_automatic_decision(self.verification, assessment)
        self.assertEqual(result.pk, decision.pk)
        decision.refresh_from_db()
        self.assertEqual(decision.reason_code, "prior_route")
        self.assertEqual(decision.decision, "manual_review_required")
        conflict = AuditEvent.objects.get(
            action="verification.automatic_decision_conflict"
        )
        self.assertEqual(conflict.metadata_json["reason"], "stale_revision")

    def test_country_document_actions_apply_only_from_the_case_snapshot(self):
        from apps.risk.services import evaluate_risk_assessment

        self.identity_document.expires_at = timezone.now().date() - timedelta(days=1)
        self.identity_document.save(update_fields=["expires_at"])
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            liveness_type="passive",
            status=LivenessCheckStatus.PASSED,
            score=Decimal("0.97"),
            checked_at=timezone.now(),
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=self.selfie_capture,
            identity_document=self.identity_document,
            document_capture=self.document_capture,
            status=FaceMatchStatus.MATCHED,
            match_score=Decimal("0.96"),
            matched_at=timezone.now(),
        )
        for action, expected in (
            ("ignore", RiskRecommendation.APPROVE),
            ("manual_review", RiskRecommendation.MANUAL_REVIEW),
            ("reject", RiskRecommendation.REJECT),
        ):
            with self.subTest(action=action):
                self.verification.policy_snapshot_json = {
                    "version": 5,
                    "document_consistency_rules": {
                        "version": 1,
                        "countries": {"*": {"actions": {"document_expired": action}}},
                    },
                }
                assessment = evaluate_risk_assessment(self.verification)
                self.assertEqual(assessment.recommendation, expected)
                self.assertEqual(
                    assessment.signals_json["document_consistency"]["policy_version"], 5
                )
        LivenessCheck.objects.filter(verification=self.verification).update(
            status=LivenessCheckStatus.FAILED
        )
        self.verification.policy_snapshot_json["document_consistency_rules"][
            "countries"
        ]["*"]["actions"]["document_expired"] = "manual_review"
        self.assertEqual(
            evaluate_risk_assessment(self.verification).recommendation,
            RiskRecommendation.REJECT,
        )
