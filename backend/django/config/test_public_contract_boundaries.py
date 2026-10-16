from django.test import SimpleTestCase
from rest_framework.test import APIClient

from config.api_views import OPENAPI_SPEC_PATH
from config.openapi_contract import (
    CONTRACT_MANAGED_PREFIXES,
    CONTRACT_MANAGED_ROUTES,
    load_contract,
    public_resources,
    registered_public_operations,
)


class HistoricalPublicContractBoundaryTests(SimpleTestCase):
    def setUp(self):
        self.contract = load_contract(OPENAPI_SPEC_PATH)

    def test_authorization_includes_client_id_for_every_api_client_operation(self):
        scheme = self.contract["components"]["securitySchemes"]["apiClientId"]
        self.assertEqual(scheme["type"], "apiKey")
        self.assertEqual(scheme["in"], "header")
        self.assertEqual(scheme["name"], "X-Client-Id")
        client_operations = 0
        for resource in public_resources(self.contract):
            for requirement in resource["security"]:
                if "apiClient" in requirement:
                    client_operations += 1
                    self.assertIn("apiClientId", requirement)
        self.assertGreater(client_operations, 0)

    def test_catalog_authentication_session_and_audit_boundaries_are_managed(self):
        self.assertTrue(
            {"api/v1/auth/", "api/v1/sessions/", "api/v1/audit-events/"}.issubset(
                CONTRACT_MANAGED_PREFIXES
            )
        )
        self.assertTrue(
            {
                "api/v1/countries",
                "api/v1/country-profiles",
                "api/v1/document-types",
            }.issubset(CONTRACT_MANAGED_ROUTES)
        )
        operations = registered_public_operations()
        self.assertTrue(
            {
                ("GET", "/countries"),
                ("GET", "/country-profiles"),
                ("GET", "/document-types"),
                ("GET", "/audit-events/"),
                ("POST", "/auth/login"),
                ("POST", "/auth/refresh"),
                ("GET", "/auth/me"),
                ("GET", "/sessions/{session_id}"),
            }.issubset(operations)
        )

    def test_actual_docs_overview_preserves_curated_endpoint_slugs(self):
        response = APIClient().get("/api/v1/docs/overview")
        self.assertEqual(response.status_code, 200)
        resources = {
            (r["method"], r["path"]): r for r in response.data["data"]["resources"]
        }
        for operation, slug in (
            (("GET", "/health"), "health"),
            (("GET", "/policies/"), "list-policies"),
            (("POST", "/verifications/"), "create-verification"),
        ):
            self.assertEqual(resources[operation]["slug"], slug)

    def test_actual_docs_overview_preserves_required_instantiation_header(self):
        response = APIClient().get("/api/v1/docs/overview")
        resource = next(
            r
            for r in response.data["data"]["resources"]
            if (r["method"], r["path"])
            == ("POST", "/projects/{project_id}/workflows:instantiate")
        )
        self.assertIn("Idempotency-Key", resource["required_headers"])
