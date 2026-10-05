from copy import deepcopy

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError as APIValidationError
from rest_framework.test import APIClient

from apps.accounts.models import PlatformUser
from apps.verification_policies.models import VerificationPolicy
from apps.verifications import tests as fixtures
from apps.verifications.result_contract import serialize_verification_result
from apps.verifications.review_reasons import (
    validate_reason_rules,
    validate_reviewer_input,
)
from apps.verifications.serializers import ManualReviewDecisionSerializer

RULES = {
    "version": 1,
    "outcomes": {
        "verified": {
            "codes": ["evidence_confirmed", "internal_override"],
            "notes_required": False,
        },
        "rejected": {"codes": ["evidence_mismatch"], "notes_required": True},
        "failed": {"codes": ["evidence_unavailable"], "notes_required": True},
    },
    "organization_facing_codes": ["evidence_confirmed", "evidence_mismatch"],
}


class ReviewerReasonTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def configure(self, *, checker=False):
        case = self.platform_case
        case.policy_snapshot_json = {
            "review_reason_rules": deepcopy(RULES),
            "maker_checker_required": checker,
        }
        case.save(update_fields=["policy_snapshot_json"])
        return case

    def decide(self, outcome, code, notes="", *, checker=False):
        case = self.configure(checker=checker)
        serializer = ManualReviewDecisionSerializer(
            data={"decision": outcome, "reason_code": code, "reason_detail": notes}
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(verification=case, decided_by=self.platform_reviewer)

    def test_outcome_requires_configured_code_and_notes_without_mutation(self):
        for code, notes in [
            ("evidence_confirmed", "Reason"),
            ("evidence_mismatch", ""),
        ]:
            with self.assertRaises(APIValidationError):
                self.decide("rejected", code, notes)
            self.platform_case.refresh_from_db()
            self.assertIsNone(self.platform_case.assigned_reviewer_id)
            self.assertFalse(hasattr(self.platform_case, "decision_record"))
        decision = self.decide(
            "rejected", "evidence_mismatch", "Evidence does not match."
        )
        self.assertEqual(decision.reason_codes_json, ["evidence_mismatch"])

    def test_plain_and_encoded_markup_are_rejected(self):
        case = self.configure()
        for notes in [
            "<script>alert(1)</script>",
            "&lt;img src=x&gt;",
            "&amp;lt;b&amp;gt;",
            "text\x00payload",
        ]:
            with self.subTest(notes=notes), self.assertRaises(ValidationError):
                validate_reviewer_input(case, "rejected", "evidence_mismatch", notes)

    def test_catalog_rejects_unknown_fields_types_duplicates_and_unapproved_codes(self):
        bad = []
        value = deepcopy(RULES)
        value["outcomes"]["rejected"]["notes_required"] = "yes"
        bad.append(value)
        value = deepcopy(RULES)
        value["organization_facing_codes"].append("outside_catalog")
        bad.append(value)
        value = deepcopy(RULES)
        value["outcomes"]["verified"]["codes"] = ["same", "same"]
        bad.append(value)
        value = deepcopy(RULES)
        value["version"] = True
        bad.append(value)
        value = deepcopy(RULES)
        value["outcomes"]["rejected"]["codes"] = [{"unsafe": 1}]
        bad.append(value)
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_reason_rules(value)
        self.assertEqual(validate_reason_rules(RULES), RULES)

    def test_public_result_only_contains_approved_codes_and_never_notes(self):
        decision = self.decide(
            "verified", "internal_override", "Internal private reviewer note"
        )
        self.platform_case.refresh_from_db()
        result = serialize_verification_result(self.platform_case)
        self.assertEqual(result["decision"]["reason_codes"], [])
        self.assertNotIn("Internal private reviewer note", str(result))
        decision.reason_codes_json = ["internal_override", "evidence_confirmed"]
        decision.save(update_fields=["reason_codes_json"])
        self.platform_case.refresh_from_db()
        self.assertEqual(
            serialize_verification_result(self.platform_case)["decision"][
                "reason_codes"
            ],
            ["evidence_confirmed"],
        )

    def test_checker_uses_final_outcome_catalog_and_own_notes(self):
        self.decide("verified", "evidence_confirmed", checker=True)
        checker = PlatformUser.objects.create_user(
            email="second-reviewer@example.test",
            password="StrongPassword123!",
            status="active",
            is_platform_admin=True,
        )
        client = APIClient()
        client.force_authenticate(checker)
        url = reverse(
            "manual-review-approval",
            kwargs={"verification_id": self.platform_case.public_id},
        )
        self.assertEqual(
            client.post(url, {"decision": "rejected"}, format="json").status_code, 400
        )
        response = client.post(
            url,
            {
                "decision": "rejected",
                "reason_code": "evidence_mismatch",
                "reason_detail": "Independent evidence assessment",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.platform_case.refresh_from_db()
        record = self.platform_case.decision_record
        self.assertEqual(record.reason_code, "evidence_mismatch")
        self.assertEqual(record.reason_detail, "Independent evidence assessment")
        self.assertEqual(record.proposed_decision, "verified")

    def test_model_writes_validate_rules_and_snapshot_keeps_approved_version(self):
        policy = VerificationPolicy(
            tenant=self.tenant,
            created_by=self.tenant_reviewer,
            name="Reason rules",
            review_reason_rules_json=deepcopy(RULES),
        )
        policy.save()
        snapshot = policy.snapshot()
        policy.review_reason_rules_json = {"version": 2}
        with self.assertRaises(ValidationError):
            policy.save()
        self.assertEqual(snapshot["review_reason_rules"], RULES)

    def test_policy_api_roundtrips_rules_and_rejects_invalid_catalog(self):
        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        url = reverse("verification-policy-list-create")
        data = {
            "name": "Reason policy",
            "required_document_types": ["passport"],
            "required_liveness_level": "passive",
            "face_match_threshold": "0.85",
            "manual_review_threshold": "0.65",
            "review_reason_rules": RULES,
            "verification_expiry_minutes": 1440,
            "media_retention_days": 30,
            "metadata_retention_days": 365,
        }
        response = client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        detail = client.get(
            reverse(
                "verification-policy-detail",
                kwargs={"policy_id": response.data["data"]["id"]},
            )
        )
        self.assertEqual(detail.data["data"]["review_reason_rules"], RULES)
        policy = VerificationPolicy.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(policy.snapshot()["review_reason_rules"], RULES)
        data["review_reason_rules"] = {"version": 2}
        self.assertEqual(client.post(url, data, format="json").status_code, 400)

    def test_legacy_plain_text_submission_has_no_implicit_public_reason(self):
        serializer = ManualReviewDecisionSerializer(
            data={
                "decision": "verified",
                "reason_code": "legacy_internal",
                "reason_detail": "Plain notes",
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(
            verification=self.platform_case, decided_by=self.platform_reviewer
        )
        self.platform_case.refresh_from_db()
        self.assertEqual(
            serialize_verification_result(self.platform_case)["decision"][
                "reason_codes"
            ],
            [],
        )
