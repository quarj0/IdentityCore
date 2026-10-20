from copy import deepcopy
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from types import SimpleNamespace
from rest_framework.exceptions import ValidationError

from apps.biometrics.models import LivenessChallenge, LivenessCheckStatus
from apps.biometrics import test_historical_evidence as historical
from apps.biometrics import tests as fixtures
from apps.verifications.models import VerificationStatus
from shared.liveness_challenge import PROTOCOL


class OrderedChallengeFinalizationTests(TestCase):
    setUp = fixtures.BiometricsTaskTests.setUp
    run_result = historical.HistoricalBiometricEvidenceTests.run_result

    def make_active(self):
        self.challenge = LivenessChallenge.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            actions=[
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
            ],
            expires_at=timezone.now() + timedelta(minutes=3),
        )
        self.liveness_check.liveness_type = "active"
        self.liveness_check.challenge = self.challenge
        self.liveness_check.save()
        self.selfie_capture.capture_type = "video"
        self.selfie_capture.save()

    def evidence(self):
        return {
            "status": "completed",
            "passed": True,
            "score": 0.94,
            "confidence_level": "high",
            "model_name": "synthetic-liveness",
            "model_version": "ordered-test",
            "challenge_id": self.challenge.public_id,
            "challenge_protocol": PROTOCOL,
            "challenge_passed": True,
            "metrics": {
                "face_count": 1,
                "avg_detection_confidence": 0.97,
                "challenge_actions": self.challenge.actions,
                "detected_actions": self.challenge.actions,
            },
        }

    def test_bound_ordered_success_can_finalize(self):
        self.make_active()
        self.run_result(result=self.evidence())
        self.liveness_check.refresh_from_db()
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.PASSED)

    def test_claimed_success_with_wrong_order_routes_to_review(self):
        self.make_active()
        result = deepcopy(self.evidence())
        result["metrics"]["detected_actions"] = [
            "look_up",
            "turn_left",
            "turn_right",
            "look_down",
            "turn_left",
        ]
        self.assertEqual(
            self.run_result(result=result), VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        self.liveness_check.refresh_from_db()
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.ERROR)

    def test_unbound_recovered_result_cannot_finalize_as_passed(self):
        self.make_active()
        result = self.evidence()
        result.pop("challenge_id")
        # The task validates cached/recovered evidence after the provider call seam.
        from unittest.mock import patch

        with patch(
            "apps.biometrics.tasks._completed_provider_result", return_value=result
        ):
            self.assertEqual(
                self.run_result(), VerificationStatus.MANUAL_REVIEW_REQUIRED
            )
        self.liveness_check.refresh_from_db()
        self.assertEqual(self.liveness_check.status, LivenessCheckStatus.ERROR)

    def test_challenge_budget_cannot_be_reset_by_session_replacement_or_soft_deletion(
        self,
    ):
        from apps.verification_sessions.serializers import (
            VerificationSessionLivenessChallengeSerializer,
        )
        from shared.liveness_challenge import MAX_CHALLENGES, valid_actions

        self.verification.policy_snapshot_json = {"required_liveness_level": "active"}
        self.verification.save()
        self.session.verification = self.verification
        request = SimpleNamespace(verification_session=self.session)
        for _ in range(MAX_CHALLENGES):
            serializer = VerificationSessionLivenessChallengeSerializer(
                data={}, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            challenge = serializer.save()
            self.assertTrue(valid_actions(challenge.actions))
        LivenessChallenge.objects.filter(verification=self.verification).update(
            deleted_at=timezone.now()
        )
        replacement = self.verification.sessions.create(
            tenant=self.tenant,
            session_token_hash="synthetic-replacement",
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        replacement.verification = self.verification
        request.verification_session = replacement
        serializer = VerificationSessionLivenessChallengeSerializer(
            data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save()
