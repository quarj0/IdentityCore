from copy import deepcopy

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.risk.test_reuse import RULES
from apps.verification_policies import tests as policy_tests
from apps.verification_policies.models import VerificationPolicy
from apps.verification_policies.serializers import VerificationPolicyUpdateSerializer


class ReusePolicyTests(APITestCase):
    setUp = policy_tests.VerificationPolicyAPITests.setUp

    def payload(self):
        return {
            "name": "Reuse policy",
            "required_document_types": ["passport"],
            "required_liveness_level": "passive",
            "face_match_threshold": "0.85",
            "manual_review_threshold": "0.65",
            "verification_expiry_minutes": 60,
            "media_retention_days": 7,
            "metadata_retention_days": 30,
            "reuse_rules": deepcopy(RULES),
        }

    def test_create_clone_snapshot_and_partial_update_preserve_rules(self):
        response = self.client.post(
            reverse("verification-policy-list-create"), self.payload(), format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        policy = VerificationPolicy.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(policy.snapshot()["reuse_rules"], RULES)
        self.assertEqual(
            self.client.get(
                reverse(
                    "verification-policy-detail", kwargs={"policy_id": policy.public_id}
                )
            ).data["data"]["reuse_rules"],
            RULES,
        )
        serializer = VerificationPolicyUpdateSerializer(
            instance=policy,
            data={"name": "Renamed"},
            context={"request": type("Request", (), {"user": self.user})()},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(policy.reuse_rules_json, RULES)
        response = self.client.post(
            reverse(
                "verification-policy-clone", kwargs={"policy_id": policy.public_id}
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        clone = VerificationPolicy.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(clone.snapshot()["reuse_rules"], RULES)

    def test_unsafe_rule_configuration_rejects_policy_creation(self):
        payload = self.payload()
        payload["reuse_rules"]["thresholds"]["device"] = True
        response = self.client.post(
            reverse("verification-policy-list-create"), payload, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("reuse_rules", response.data["error"]["details"])
