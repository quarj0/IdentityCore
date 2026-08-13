import yaml
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from config.api_views import OPENAPI_SPEC_PATH


class CatalogEndpointTests(APITestCase):
    def test_health_identifies_the_public_api_service(self):
        response = self.client.get("/api/v1/health")
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["service"], "identitycore-api")

    def test_health_rejects_undeclared_methods(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)("/api/v1/health")
                self.assertEqual(
                    response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_countries_returns_full_public_catalog(self):
        response = self.client.get(reverse("country-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        country_map = {item["code"]: item["name"] for item in response.data["data"]}
        self.assertEqual(country_map["GH"], "Ghana")
        self.assertIn("NG", country_map)
        self.assertIn("US", country_map)
        self.assertTrue(all(len(code) == 2 for code in country_map))

    def test_document_types_returns_bootstrap_catalog(self):
        response = self.client.get(reverse("document-type-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"][0]["code"], "national_id")

    def test_country_profiles_returns_bootstrap_catalog(self):
        response = self.client.get(reverse("country-profile-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"][0]["code"], "GH")
        self.assertEqual(
            response.data["data"][0]["supported_document_types"][0]["document_type"],
            "national_id",
        )

    def test_docs_overview_returns_public_api_metadata(self):
        response = self.client.get(reverse("docs-overview"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["api_version"], "1.0")
        self.assertEqual(
            data["base_urls"]["development"], "http://localhost:8000/api/v1"
        )
        self.assertEqual(len(data["resources"]), 61)
        self.assertIn("/verifications/", [item["path"] for item in data["resources"]])
        documented_paths = {item["path"] for item in data["resources"]}
        self.assertTrue(
            {
                "/uploads/",
                "/document-types",
                "/country-profiles",
                "/countries",
                "/sessions/{session_id}",
                "/sessions/{session_id}/consent",
                "/sessions/{session_id}/status",
                "/sessions/mobile-handoff/redeem",
                "/organization/me/",
                "/organization/me/verification-documents/{document_id}/content/",
                "/organization/me/suspend",
                "/projects/",
                "/projects/{project_id}/workflows:instantiate",
                "/api-clients/",
                "/webhook-endpoints/",
                "/verifications/manual-reviews",
                "/verifications/manual-reviews/{verification_id}/approval",
                "/verifications/{verification_id}/result",
                "/verifications/{verification_id}/evidence-report/download.pdf",
            }.issubset(documented_paths)
        )
        sdk_status = {item["language"]: item["status"] for item in data["sdk_status"]}
        self.assertEqual(sdk_status["python"], "ready")
        self.assertEqual(sdk_status["javascript"], "ready")
        self.assertEqual(sdk_status["java"], "ready")
        self.assertEqual(sdk_status["csharp"], "ready")
        self.assertEqual(data["spec_url"], "/api/v1/docs/openapi.yaml")
        create_verification = next(
            item
            for item in data["resources"]
            if (item["method"], item["path"]) == ("POST", "/verifications/")
        )
        self.assertEqual(create_verification["slug"], "create-verification")
        countries = next(
            item
            for item in data["resources"]
            if (item["method"], item["path"]) == ("GET", "/countries")
        )
        self.assertEqual(countries["security"], [])

    def test_openapi_spec_returns_public_yaml(self):
        response = self.client.get(reverse("openapi-spec"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.content.decode("utf-8")
        self.assertIn("openapi: 3.1.0", body)
        self.assertIn("IdentityCore Public API", body)
        self.assertIn("/uploads/", body)
        self.assertIn("/organization/me/", body)
        self.assertIn(
            "/organization/me/verification-documents/{document_id}/content/", body
        )
        self.assertIn("/organization/me/suspend", body)
        self.assertIn("/projects/{project_id}/workflows:instantiate", body)
        self.assertIn("/api-clients/", body)
        self.assertIn("/verifications/manual-reviews", body)
        self.assertIn("/verifications/{verification_id}/result", body)

    def test_newly_documented_backend_routes_are_registered(self):
        routes = [
            ("post", "/api/v1/organization/me/suspend"),
            ("put", "/api/v1/organization/me/verification-documents/doc_123/content/"),
            ("post", "/api/v1/projects/prj_123/workflows:instantiate"),
        ]

        for method, path in routes:
            with self.subTest(method=method, path=path):
                response = getattr(self.client, method)(path, {}, format="json")
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OpenApiAuthenticationContractTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.contract = yaml.safe_load(OPENAPI_SPEC_PATH.read_text(encoding="utf-8"))

    def test_api_client_auth_requires_bearer_secret_and_client_id(self):
        schemes = self.contract["components"]["securitySchemes"]

        self.assertEqual(
            self.contract["security"],
            [{"apiClient": [], "apiClientId": []}],
        )
        self.assertEqual(
            schemes["apiClientId"],
            {
                "type": "apiKey",
                "in": "header",
                "name": "X-Client-Id",
                "description": "Send the API client ID with the bearer API client secret.",
            },
        )

    def test_authentication_exceptions_remain_explicit(self):
        paths = self.contract["paths"]

        self.assertEqual(paths["/health"]["get"]["security"], [])
        verification_session_security = [
            {"verificationSessionBearer": [], "verificationSessionId": []}
        ]
        for upload_path in (
            "/uploads/",
            "/uploads/{upload_id}/transfer",
            "/uploads/{upload_id}/complete",
        ):
            self.assertEqual(
                paths[upload_path]["post"]["security"],
                verification_session_security,
            )
        schemes = self.contract["components"]["securitySchemes"]
        self.assertNotIn("platformUserSession", schemes)
        self.assertEqual(
            schemes["verificationSessionId"],
            {
                "type": "apiKey",
                "in": "header",
                "name": "X-Session-Id",
                "description": "Verification session identifier required when it is not present in the URL path.",
            },
        )
        self.assertEqual(
            paths["/auth/refresh"]["post"]["security"],
            [{"platformRefreshCookie": []}],
        )

    def test_client_id_is_not_duplicated_as_an_operation_parameter(self):
        parameters = self.contract["components"]["parameters"]

        self.assertNotIn("ClientIdHeader", parameters)
        self.assertNotIn(
            "#/components/parameters/ClientIdHeader",
            OPENAPI_SPEC_PATH.read_text(encoding="utf-8"),
        )
