from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.biometrics import test_finalization_recovery as biometric_fixtures
from apps.biometrics.tasks import process_verification_biometrics_task
from apps.providers import test_route_final_action_ownership as route_fixtures
from apps.providers.models import ProviderCheckType
from apps.providers.services import _apply_route_final_action
from apps.verifications import test_processing_jobs as processing_fixtures
from apps.verifications.decision_contract import build_decision_input_snapshot
from apps.verifications.models import (
    ProcessingJobStatus,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)
from apps.verifications.processing_jobs import (
    exhaust_processing_job,
    queue_identity_document_processing,
)


class SystemDecisionContractAssertions(TestCase):
    def seed_stale_contract(self):
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            decision=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            decision_type=VerificationDecisionType.AUTOMATIC,
            reason_code="risk_rules_manual_review",
            reason_codes_json=["old_reason"],
            contract_version="legacy",
            input_snapshot_json={"stale": True},
            decided_at=timezone.now(),
        )

    def assert_current_contract(self, reason):
        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(decision.decision_type, VerificationDecisionType.SYSTEM)
        self.assertEqual(decision.reason_code, reason)
        self.assertEqual(decision.reason_codes_json, [reason])
        self.assertEqual(decision.contract_version, "1")
        self.assertEqual(
            decision.input_snapshot_json,
            build_decision_input_snapshot(self.verification),
        )
        self.assertNotIn("stale", decision.input_snapshot_json)


class BiometricSystemDecisionContractTests(SystemDecisionContractAssertions):
    setUp = biometric_fixtures.BiometricFinalizationRecoveryTests.setUp

    @patch("apps.biometrics.tasks.queue_verification_status_notifications")
    @patch("apps.biometrics.tasks.queue_webhook_events")
    @patch("apps.uploads.services._move_upload_to_media_bucket")
    @patch(
        "apps.biometrics.tasks.run_liveness_check",
        side_effect=RuntimeError("provider unavailable"),
    )
    def test_unavailable_fallback_replaces_the_contract(self, *_mocks):
        self.seed_stale_contract()
        self.assertEqual(
            process_verification_biometrics_task(self.liveness_check.public_id),
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.assert_current_contract("biometric_provider_unavailable")


class ProcessingSystemDecisionContractTests(SystemDecisionContractAssertions):
    setUp = processing_fixtures.ProcessingJobRecoveryTests.setUp

    def test_retry_exhaustion_replaces_the_contract(self):
        self.seed_stale_contract()
        job = queue_identity_document_processing(self.identity_document)
        exhaust_processing_job(job)
        self.assert_current_contract("processing_retries_exhausted")

    def test_retry_after_subject_erasure_preserves_empty_inputs(self):
        from apps.providers.models import ProviderCheckStatus
        from apps.providers.services import create_provider_check
        from apps.verification_subjects.services import request_subject_deletion

        self.seed_stale_contract()
        create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            normalized_result={
                "workflow_result": {
                    "extracted_fields": {"full_name": "Private erased name"}
                }
            },
        )
        self.assertEqual(
            request_subject_deletion(subject=self.subject)["status"], "completed"
        )
        # The caller may still have a pre-erasure subject cached on its case.
        job = queue_identity_document_processing(self.identity_document)
        exhaust_processing_job(job)
        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(decision.reason_codes_json, ["processing_retries_exhausted"])
        self.assertEqual(decision.input_snapshot_json, {})


class RouteSystemDecisionContractTests(SystemDecisionContractAssertions):
    setUp = route_fixtures.RouteFinalActionOwnershipTests.setUp
    _job = route_fixtures.RouteFinalActionOwnershipTests._job

    def test_route_exhaustion_replaces_the_contract(self):
        self.seed_stale_contract()
        self._job(ProcessingJobStatus.PROCESSING)
        _apply_route_final_action(
            verification=self.verification,
            route=None,
            check_type=ProviderCheckType.LIVENESS,
            attempts=[self.attempt],
        )
        self.assert_current_contract("provider_route_exhausted")
