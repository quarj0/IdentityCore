import json
from datetime import datetime, timezone

from django.test import SimpleTestCase, TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.api_clients.models import APIIdempotencyRecord
from apps.claims import tests as fixtures
from apps.claims.disclosure import retire_policy
from apps.claims.models import ClaimDisclosureRedemption
from apps.claims.rules import apply_rule
from apps.evidence.access import GovernedContentUnavailable


class DisclosureAPITests(TestCase):
    propose = fixtures.ClaimsTests.propose
    create_evidence = fixtures.ClaimsTests.create_evidence
    claim = fixtures.ClaimsTests.claim
    normalized = fixtures.ClaimsTests.normalized
    policy = fixtures.ClaimsTests.policy

    def setUp(self):
        fixtures.ClaimsTests.setUp(self)
        self.client = APIClient()
        self.client.force_authenticate(self.maker)

    def test_issue_replay_never_recovers_token_and_redemption_values_are_not_cached(
        self,
    ):
        claim, policy = self.normalized(), self.policy()
        body = {
            "project_id": self.project.public_id,
            "authorization_id": self.claim_auth.public_id,
            "audience_id": self.audience.public_id,
            "selections": [
                {
                    "claim_id": claim.public_id,
                    "policy_id": policy.public_id,
                    "fields": ["name"],
                }
            ],
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "issue-disclosure-once"}
        first = self.client.post(
            "/api/v1/claims/disclosures", body, format="json", **headers
        )
        self.assertEqual(first.status_code, 201, first.data)
        token = first.data["data"]["token"]
        self.assertTrue(token)
        replay = self.client.post(
            "/api/v1/claims/disclosures", body, format="json", **headers
        )
        self.assertEqual(replay.status_code, 201, replay.data)
        self.assertIsNone(replay.data["data"]["token"])
        self.assertFalse(replay.data["data"]["token_available"])
        for record in APIIdempotencyRecord.objects.all():
            self.assertNotIn(token, json.dumps(record.response_data_json))
            self.assertNotIn(
                "Synthetic applicant", json.dumps(record.response_data_json)
            )
        path = f'/api/v1/claims/disclosures/{first.data["data"]["id"]}/redeem'
        self.client.force_authenticate(user=None)
        recipient_headers = {
            "HTTP_X_CLIENT_ID": self.audience.client_id,
            "HTTP_AUTHORIZATION": "Bearer synthetic-recipient-secret",
            "HTTP_X_DISCLOSURE_TOKEN": token,
            "HTTP_IDEMPOTENCY_KEY": "redeem-once",
        }
        response = self.client.post(
            path,
            {"project_id": self.project.public_id},
            format="json",
            **recipient_headers,
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["data"]["claims"][0]["value"], {"name": "Synthetic applicant"}
        )
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(ClaimDisclosureRedemption.objects.count(), 1)
        self.assertEqual(APIIdempotencyRecord.objects.count(), 1)
        retire_policy(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            project_id=self.project.public_id,
            policy_id=policy.public_id,
        )
        rejected = self.client.post(
            path,
            {"project_id": self.project.public_id},
            format="json",
            **recipient_headers,
        )
        self.assertEqual(rejected.status_code, 403, rejected.data)
        self.assertNotIn("Synthetic applicant", json.dumps(rejected.data))

    def test_unknown_body_fields_do_not_silently_change_claim_meaning(self):
        response = self.client.post(
            "/api/v1/claims/disclosures",
            {"project_id": self.project.public_id, "unrecognized": True},
            format="json",
            HTTP_IDEMPOTENCY_KEY="invalid-body",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(APIIdempotencyRecord.objects.exists())


class DeterministicRuleTests(SimpleTestCase):
    def rule(self, name, value, **parameters):
        return apply_rule(
            name,
            1,
            [{"input": value}],
            {"field": "input", **parameters},
            now=datetime(2026, 2, 28, 23, 59, tzinfo=timezone.utc),
        )

    def test_age_predicate_expires_at_utc_midnight_and_uses_calendar_age(self):
        value, kind, deadline = self.rule("age_over", "2008-02-29", threshold=18)
        self.assertEqual(value, {"value": False})
        self.assertEqual(kind, "derived")
        self.assertEqual(deadline, datetime(2026, 3, 1, tzinfo=timezone.utc))
        self.assertEqual(
            self.rule("age_over", "2008-02-28", threshold=18)[0], {"value": True}
        )
        for threshold in (True, -1, 121, "18"):
            with self.subTest(threshold=threshold), self.assertRaises(ValidationError):
                self.rule("age_over", "2000-01-01", threshold=threshold)

    def test_expiry_includes_printed_expiry_date_and_rejects_invalid_dates(self):
        self.assertEqual(
            self.rule("document_current", "2026-02-28")[0], {"value": True}
        )
        self.assertEqual(
            self.rule("document_current", "2026-02-27")[0], {"value": False}
        )
        for value in ("2026-02-29", "26-02-28", "2026-02-28T00:00:00Z", None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.rule("iso_date", value)

    def test_content_failure_has_a_stable_non_disclosing_service_error(self):
        from apps.evidence.access import protected_value

        class BrokenRecord:
            @property
            def value_json(self):
                raise ValueError("key provider details and sensitive material")

        with self.assertRaises(GovernedContentUnavailable) as error:
            protected_value(BrokenRecord(), "value_json")
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn("key provider", str(error.exception))
