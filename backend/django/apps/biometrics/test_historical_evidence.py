from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import LivenessCheckStatus
from apps.biometrics.tasks import process_verification_biometrics_task
from apps.biometrics import tests as biometric_fixtures
from apps.providers.ai_service import AIServiceUnavailable
from apps.providers.models import ProviderCheckStatus
from apps.verifications.models import (
    ProcessingJob,
    VerificationDecision,
    VerificationStatus,
)
from apps.verifications.processing_jobs import ProcessingJobOwnershipLost


class HistoricalBiometricEvidenceTests(TestCase):
    setUp = biometric_fixtures.BiometricsTaskTests.setUp

    def run_result(self, *, result=None, error=None, face_error=None):
        liveness = {
            "status": "completed",
            "score": 0.94,
            "confidence_level": "high",
            "passed": True,
            "model_name": "mock-liveness",
            "model_version": "v1",
            "metrics": {"face_count": 1, "avg_detection_confidence": 0.97},
        }
        face = {
            "status": "completed",
            "match_score": 0.96,
            "confidence_level": "high",
            "matched": True,
            "threshold_used": 0.85,
            "model_name": "mock-face-match",
            "model_version": "v1",
        }
        with (
            patch(
                "apps.biometrics.tasks.run_liveness_check",
                return_value=result or liveness,
                side_effect=error,
            ),
            patch(
                "apps.biometrics.tasks.run_face_compare",
                return_value=face,
                side_effect=face_error,
            ),
        ):
            return process_verification_biometrics_task(self.liveness_check.public_id)

    def invalid_evidence(self, **fields):
        result = {
            "status": "completed",
            "passed": True,
            "score": 0.94,
            "model_name": "mock-liveness",
            "model_version": "v1",
            "metrics": {"face_count": 1, "avg_detection_confidence": 0.97},
        }
        result.update(deepcopy(fields))
        self.assertEqual(
            self.run_result(result=result), VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        self.liveness_check.refresh_from_db()
        self.liveness_provider_check.refresh_from_db()
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.ERROR)
        self.assertEqual(
            self.liveness_provider_check.error_code, "provider_invalid_response"
        )
        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(
            decision.evidence_summary_json["provider_error"],
            "provider_invalid_response",
        )

    def test_negative_detection_confidence_is_contract_failure(self):
        self.invalid_evidence(
            metrics={"face_count": 1, "avg_detection_confidence": -0.1}
        )

    def test_confidence_above_one_is_contract_failure(self):
        self.invalid_evidence(
            metrics={"face_count": 1, "avg_detection_confidence": 1.1}
        )

    def test_boolean_confidence_is_contract_failure(self):
        self.invalid_evidence(
            metrics={"face_count": 1, "avg_detection_confidence": True}
        )

    def test_nonfinite_confidence_is_contract_failure(self):
        self.invalid_evidence(
            metrics={"face_count": 1, "avg_detection_confidence": float("inf")}
        )

    def test_model_name_must_be_string(self):
        self.invalid_evidence(model_name={"provider": "unexpected"})

    def test_model_version_must_fit_storage(self):
        self.invalid_evidence(model_version="v" * 300)

    def test_missing_detection_evidence_is_contract_failure(self):
        self.invalid_evidence(metrics={})

    def test_rejected_face_count_has_failure_reason(self):
        self.run_result(
            result={
                "status": "completed",
                "passed": True,
                "score": 0.94,
                "model_name": "mock-liveness",
                "model_version": "v1",
                "metrics": {"face_count": 2, "avg_detection_confidence": 0.97},
            }
        )
        self.liveness_check.refresh_from_db()
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.FAILED)
        self.assertTrue(self.liveness_check.failure_reason)

    def test_timeout_keeps_provider_classification(self):
        self.run_result(
            error=AIServiceUnavailable(
                error_code="provider_timeout",
                provider_check_status=ProviderCheckStatus.TIMEOUT,
            )
        )
        self.liveness_provider_check.refresh_from_db()
        self.assertEqual(
            self.liveness_provider_check.status, ProviderCheckStatus.TIMEOUT
        )
        self.assertEqual(self.liveness_provider_check.error_code, "provider_timeout")
        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(
            decision.evidence_summary_json["provider_error"], "provider_timeout"
        )

    def test_nan_confidence_is_contract_failure(self):
        self.invalid_evidence(
            metrics={"face_count": 1, "avg_detection_confidence": float("nan")}
        )

    def test_model_name_must_fit_storage(self):
        self.invalid_evidence(model_name="m" * 121)

    def test_model_version_must_be_string(self):
        self.invalid_evidence(model_version=123)

    def test_metrics_must_be_object(self):
        self.invalid_evidence(metrics=[1, 0.97])

    def test_missing_provider_links_are_created_and_saved(self):
        self.liveness_check.provider_check_id = ""
        self.liveness_check.save(update_fields=["provider_check_id"])
        self.face_match.provider_check_id = ""
        self.face_match.save(update_fields=["provider_check_id"])
        self.assertEqual(self.run_result(), VerificationStatus.VERIFIED)
        self.liveness_check.refresh_from_db()
        self.face_match.refresh_from_db()
        for resource in (self.liveness_check, self.face_match):
            self.assertTrue(resource.provider_check_id)
            self.assertTrue(
                self.verification.provider_checks.filter(
                    public_id=resource.provider_check_id,
                    status=ProviderCheckStatus.COMPLETED,
                ).exists()
            )

    def lose_owner(self):
        from django.db.models import F

        ProcessingJob.objects.filter(
            resource_public_id=self.liveness_check.public_id
        ).update(lease_generation=F("lease_generation") + 1)

    def assert_unmodified_domain(self):
        self.liveness_check.refresh_from_db()
        self.face_match.refresh_from_db()
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.INCONCLUSIVE)
        self.assertEqual(self.face_match.status, "inconclusive")
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )
        self.liveness_provider_check.refresh_from_db()
        self.assertEqual(
            self.liveness_provider_check.status, ProviderCheckStatus.PROCESSING
        )
        self.assertEqual(self.liveness_provider_check.error_code, "")

    def test_success_after_lost_ownership_cannot_write_result(self):
        def complete(**kwargs):
            self.lose_owner()
            return {
                "status": "completed",
                "passed": True,
                "score": 0.94,
                "model_name": "mock-liveness",
                "model_version": "v1",
                "metrics": {"face_count": 1, "avg_detection_confidence": 0.97},
            }

        with self.assertRaises(ProcessingJobOwnershipLost):
            self.run_result(error=complete)
        self.assert_unmodified_domain()

    def test_failure_after_lost_ownership_cannot_write_error(self):
        def fail(**kwargs):
            self.lose_owner()
            raise AIServiceUnavailable(
                error_code="provider_timeout",
                provider_check_status=ProviderCheckStatus.TIMEOUT,
            )

        with self.assertRaises(ProcessingJobOwnershipLost):
            self.run_result(error=fail)
        self.assert_unmodified_domain()

    def test_face_timeout_keeps_provider_classification(self):
        self.run_result(
            face_error=AIServiceUnavailable(
                error_code="provider_timeout",
                provider_check_status=ProviderCheckStatus.TIMEOUT,
            )
        )
        self.face_provider_check.refresh_from_db()
        self.liveness_check.refresh_from_db()
        self.assertEqual(self.face_provider_check.status, ProviderCheckStatus.TIMEOUT)
        self.assertEqual(self.face_provider_check.error_code, "provider_timeout")
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.PASSED)
        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(
            decision.evidence_summary_json["provider_error"], "provider_timeout"
        )

    def test_recovered_completed_evidence_is_revalidated(self):
        self.liveness_provider_check.status = ProviderCheckStatus.COMPLETED
        self.liveness_provider_check.completed_at = timezone.now()
        self.liveness_provider_check.normalized_result_json = {
            "contract_version": "1",
            "capability": "liveness",
            "status": "completed",
            "passed": True,
            "score": 0.94,
            "model_name": "legacy-liveness",
            "model_version": "v1",
            "metrics": {"face_count": 1, "avg_detection_confidence": -0.1},
        }
        self.liveness_provider_check.request_metadata_json = {
            "liveness_check_id": self.liveness_check.public_id
        }
        self.liveness_provider_check.save()
        self.assertEqual(self.run_result(), VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.liveness_provider_check.refresh_from_db()
        self.assertEqual(
            self.liveness_provider_check.status, ProviderCheckStatus.FAILED
        )
        self.assertEqual(
            self.liveness_provider_check.error_code, "provider_invalid_response"
        )
        self.assertEqual(
            self.liveness_provider_check.normalized_result_json["status"], "failed"
        )
        self.assertEqual(
            self.liveness_provider_check.normalized_result_json["error"]["code"],
            "provider_invalid_response",
        )
        self.assertNotIn("metrics", self.liveness_provider_check.normalized_result_json)
