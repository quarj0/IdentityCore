"""Validate actual governed API responses against the published contract."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.claims import tests as fixtures
from apps.evidence import tests as evidence_fixtures
from config.api_views import OPENAPI_SPEC_PATH
from config.openapi_contract import _validate_example, load_contract


class GovernedContractTests(TestCase):
    propose = fixtures.ClaimsTests.propose
    create_evidence = fixtures.ClaimsTests.create_evidence
    claim = fixtures.ClaimsTests.claim
    normalized = fixtures.ClaimsTests.normalized
    policy = fixtures.ClaimsTests.policy
    body = evidence_fixtures.EvidenceAPITests.body

    def setUp(self):
        fixtures.ClaimsTests.setUp(self)
        self.client = APIClient()
        self.client.force_authenticate(self.maker)
        self.contract = load_contract(OPENAPI_SPEC_PATH)

    def assert_response(self, route, method, response):
        code = str(response.status_code)
        self.assertIn(
            code, self.contract["paths"][route][method]["responses"], response.data
        )
        schema = (
            self.contract["paths"][route][method]["responses"][code]
            .get("content", {})
            .get("application/json", {})
            .get("schema")
        )
        self.assertIsNotNone(schema, response.data)
        self.assertEqual(
            _validate_example(response.data, schema, self.contract, route),
            [],
            response.data,
        )

    def test_evidence_create_payload_read_and_real_edges_match_published_response_types(
        self,
    ):
        response = self.client.post(
            "/api/v1/evidence/",
            self.body(),
            format="json",
            HTTP_IDEMPOTENCY_KEY="contract-create",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assert_response("/evidence/", "post", response)
        root = response.data["data"]["id"]
        child = self.create_evidence(source_ids=[root])
        query = {
            "project_id": self.project.public_id,
            "purpose": "eligibility",
            "include_payload": "true",
        }
        detail = self.client.get(f"/api/v1/evidence/{child.public_id}", query)
        self.assert_response("/evidence/{evidence_id}", "get", detail)
        lineage = self.client.get(f"/api/v1/evidence/{child.public_id}/lineage", query)
        self.assertEqual(len(lineage.data["data"]["edges"]), 1)
        self.assert_response("/evidence/{evidence_id}/lineage", "get", lineage)

    def test_claim_policy_evaluation_and_disclosure_receipts_match_published_types(
        self,
    ):
        claim, policy = self.normalized(), self.policy()
        query = {
            "project_id": self.project.public_id,
            "purpose": "eligibility",
            "include_value": "true",
        }
        self.assert_response(
            "/claims/{claim_id}",
            "get",
            self.client.get(f"/api/v1/claims/{claim.public_id}", query),
        )
        evaluation = self.client.post(
            f"/api/v1/claims/{claim.public_id}/evaluate",
            {
                "project_id": self.project.public_id,
                "purpose": "eligibility",
                "policy_id": policy.public_id,
            },
            format="json",
        )
        self.assert_response("/claims/{claim_id}/evaluate", "post", evaluation)
        issuance = self.client.post(
            "/api/v1/claims/disclosures",
            {
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
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="contract-issue",
        )
        self.assert_response("/claims/disclosures", "post", issuance)
        receipt = issuance.data["data"]
        self.client.force_authenticate(user=None)
        redemption = self.client.post(
            f'/api/v1/claims/disclosures/{receipt["id"]}/redeem',
            {"project_id": self.project.public_id},
            format="json",
            HTTP_X_CLIENT_ID=self.audience.client_id,
            HTTP_AUTHORIZATION="Bearer synthetic-recipient-secret",
            HTTP_X_DISCLOSURE_TOKEN=receipt["token"],
            HTTP_IDEMPOTENCY_KEY="contract-redeem",
        )
        self.assert_response(
            "/claims/disclosures/{disclosure_id}/redeem", "post", redemption
        )
