from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import FaceMatch, LivenessCheck, SelfieCapture
from apps.organizations.models import Organization
from apps.identity_documents.models import IdentityDocument
from apps.providers.adapters import ProviderContractError, provider_adapter_registry
from apps.providers.http_adapter import SecureHTTPAdapterError
from apps.providers.models import (
    Provider,
    ProviderAssignment,
    ProviderRoute,
    ProviderRouteStep,
)
from apps.providers.services import publish_provider_route
from apps.risk.external import normalize_external_risk
from apps.risk.services import (
    evaluate_risk_assessment,
    run_verification_risk_and_decision,
)
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification


def evidence(score=20, **changes):
    return {
        "contract_version": "1",
        "capability": "risk_check",
        "status": "completed",
        "risk_version": "1",
        "provider_version": "synthetic-1.0",
        "risk_score": score,
        "signals": [],
        **changes,
    }


class ExternalRiskTests(TestCase):
    def setUp(self):
        org = Organization.objects.create(name="Risk", slug="external-risk")
        self.tenant = Tenant.objects.create(
            organization=org, name="Risk", slug="external-risk", status="active"
        )
        subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="NEVER SEND SYNTHETIC NAME"
        )
        self.verification = Verification.objects.create(
            organization=org,
            tenant=self.tenant,
            verification_subject=subject,
            purpose="Synthetic",
            status="processing",
            expires_at=timezone.now() + timedelta(hours=1),
            policy_snapshot_json={
                "external_risk_enabled": True,
                "external_risk_review_threshold": 70,
                "external_risk_failure_action": "manual_review",
            },
        )
        selfie = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=subject,
            storage_key="NEVER_SEND_STORAGE",
            capture_type="image",
            captured_at=timezone.now(),
        )
        self.liveness = LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=selfie,
            status="passed",
            score=Decimal("0.95"),
            checked_at=timezone.now(),
        )
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=subject,
            document_type_id="national_id",
            status="processing",
        )
        FaceMatch.objects.create(
            identity_document=document,
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=selfie,
            status="matched",
            match_score=Decimal("0.97"),
            matched_at=timezone.now(),
        )
        self.provider = Provider.objects.create(
            tenant=self.tenant,
            name="External Risk",
            code="external-risk-v1",
            provider_type="risk",
        )
        ProviderAssignment.objects.create(
            tenant=self.tenant, provider=self.provider, assignment_key="risk_check"
        )
        self.adapter = Mock()
        self.adapter.risk_check.return_value = evidence()
        registry = patch.dict(
            provider_adapter_registry._factories,
            {self.provider.code: lambda: self.adapter},
        )
        registry.start()
        self.addCleanup(registry.stop)

    def test_high_score_is_evidence_then_policy_review_and_inputs_are_minimal(self):
        self.adapter.risk_check.return_value = evidence(90)
        assessment, decision = run_verification_risk_and_decision(self.verification)
        self.assertEqual(decision.decision, "manual_review_required")
        self.assertEqual(
            assessment.signals_json["external_risk"]["provider_version"],
            "synthetic-1.0",
        )
        self.assertEqual(assessment.risk_score, 90)
        inputs = self.adapter.risk_check.call_args.kwargs
        self.assertEqual(
            set(inputs),
            {
                "timeout_seconds",
                "input_version",
                "document_submitted",
                "document_requires_manual_review",
                "selfie_submitted",
                "liveness_status",
                "face_match_status",
            },
        )
        for private in (
            "NEVER SEND SYNTHETIC NAME",
            "NEVER_SEND_STORAGE",
            self.verification.public_id,
        ):
            self.assertNotIn(private, str(inputs))
        checks = self.verification.provider_checks.order_by("id")
        self.assertEqual(checks.first().provider_id, self.provider.id)
        self.assertEqual(checks.last().provider.code, "internal-risk-rules")
        self.assertIn("external_risk", decision.input_snapshot_json["risk_signals"])

    def test_low_score_cannot_overrule_local_rejection(self):
        self.liveness.status = "failed"
        self.liveness.save()
        self.adapter.risk_check.return_value = evidence(0)
        assessment, decision = run_verification_risk_and_decision(self.verification)
        self.assertEqual(decision.decision, "rejected")
        self.assertEqual(assessment.risk_score, 96)

    def test_unknown_output_and_direct_approval_are_rejected_before_persistence(self):
        self.adapter.risk_check.return_value = evidence(
            0, decision="approved", secret="NEVER_PERSIST"
        )
        assessment, decision = run_verification_risk_and_decision(self.verification)
        self.assertEqual(decision.decision, "manual_review_required")
        self.assertEqual(
            assessment.signals_json["external_risk"]["status"], "unavailable"
        )
        self.assertNotIn(
            "NEVER_PERSIST",
            str(
                list(self.verification.provider_checks.values("normalized_result_json"))
            ),
        )

    def test_route_exhaustion_does_not_write_a_decision_before_policy(self):
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="risk",
            name="Risk",
            environment="sandbox",
            capability="risk_check",
            final_action="fail",
        )
        ProviderRouteStep.objects.create(
            route=route, provider=self.provider, position=1
        )
        publish_provider_route(route)
        self.adapter.risk_check.side_effect = SecureHTTPAdapterError(
            "Synthetic timeout", error_code="provider_timeout", retryable=True
        )
        assessment = evaluate_risk_assessment(self.verification)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "processing")
        from apps.verifications.models import VerificationDecision

        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )
        self.assertEqual(assessment.recommendation, "manual_review")
        self.assertEqual(self.adapter.risk_check.call_count, 2)

    def test_policy_can_explicitly_ignore_unavailable_external_evidence(self):
        self.verification.policy_snapshot_json["external_risk_failure_action"] = (
            "ignore"
        )
        self.adapter.risk_check.side_effect = SecureHTTPAdapterError(
            "Synthetic error", error_code="provider_unavailable"
        )
        assessment = evaluate_risk_assessment(self.verification)
        self.assertEqual(assessment.recommendation, "approve")
        self.assertEqual(
            assessment.signals_json["external_risk"]["status"], "unavailable"
        )

    def test_inconclusive_and_invalid_threshold_fail_to_review(self):
        self.adapter.risk_check.return_value = evidence(None, status="inconclusive")
        self.verification.policy_snapshot_json["external_risk_review_threshold"] = "NaN"
        self.assertEqual(
            evaluate_risk_assessment(self.verification).recommendation, "manual_review"
        )

    def test_disabled_policy_skips_external_transport(self):
        self.verification.policy_snapshot_json["external_risk_enabled"] = False
        self.assertEqual(
            evaluate_risk_assessment(self.verification).recommendation, "approve"
        )
        self.adapter.risk_check.assert_not_called()

    def test_contract_rejects_versions_nonfinite_scores_and_unknown_signals(self):
        for payload in (
            evidence(float("nan")),
            evidence(True),
            evidence(-1),
            evidence(101),
            evidence(1, risk_version="2"),
            evidence(1, signals=["arbitrary personal text"]),
            evidence(1, capability="face_match"),
        ):
            with self.subTest(payload=payload), self.assertRaises(
                ProviderContractError
            ):
                normalize_external_risk(payload)
