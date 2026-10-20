import json
import unittest
from urllib.parse import parse_qs, urlsplit

from identitycore import IdentityCoreClient


class GovernedSDKTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def transport(method, url, headers, body, timeout):
            self.calls.append(
                (method, url, headers, json.loads(body) if body else None)
            )
            return 200, b'{"success":true,"data":{"ok":true}}'

        self.client = IdentityCoreClient(
            api_origin="https://api.example.test",
            client_id="recipient",
            client_secret="synthetic-secret",
            transport=transport,
        )

    def test_metadata_query_and_adversarial_identifier_are_encoded_as_one_segment(self):
        self.client.governed.get_evidence(
            "evd_one/../../claims?secret=value",
            query={
                "project_id": "prj_one",
                "purpose": "address & employment",
                "include_payload": False,
            },
        )
        method, url, _, body = self.calls[-1]
        parsed = urlsplit(url)
        self.assertEqual(method, "GET")
        self.assertIn("evd_one%2F..%2F..%2Fclaims%3Fsecret%3Dvalue", parsed.path)
        self.assertEqual(
            parse_qs(parsed.query),
            {
                "project_id": ["prj_one"],
                "purpose": ["address & employment"],
                "include_payload": ["False"],
            },
        )
        self.assertIsNone(body)

    def test_mutations_preserve_body_and_the_callers_idempotency_key(self):
        body = {
            "project_id": "prj_one",
            "purpose": "eligibility",
            "reason": "source_ended",
        }
        self.client.governed.revoke_claim(
            "clm_one", body, idempotency_key="revoke-once"
        )
        method, url, headers, sent = self.calls[-1]
        self.assertEqual(
            (method, url),
            ("POST", "https://api.example.test/api/v1/claims/clm_one/revoke"),
        )
        self.assertEqual(sent, body)
        self.assertEqual(headers["Idempotency-Key"], "revoke-once")

    def test_disclosure_capability_is_a_header_and_not_a_url_or_body_field(self):
        self.client.governed.redeem_claim_disclosure(
            "dcl_one",
            {"project_id": "prj_one"},
            disclosure_token="synthetic-capability",
            idempotency_key="redeem-once",
        )
        _, url, headers, body = self.calls[-1]
        self.assertNotIn("synthetic-capability", url)
        self.assertNotIn("synthetic-capability", json.dumps(body))
        self.assertEqual(headers["X-Disclosure-Token"], "synthetic-capability")
        self.assertEqual(headers["X-Client-Id"], "recipient")

    def test_privacy_approval_can_use_a_user_jwt_without_machine_credentials(self):
        self.client.access_token = "synthetic-user-jwt"
        self.client.governed.approve_purpose_authorization("paz_one", {})
        self.assertEqual(
            self.calls[-1][2]["Authorization"], "Bearer synthetic-user-jwt"
        )
        self.assertNotIn("X-Client-Id", self.calls[-1][2])
