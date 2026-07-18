from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CatalogEndpointTests(APITestCase):
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
        self.assertEqual(data["base_urls"]["development"], "http://localhost:8000/api/v1")
        self.assertIn("/verifications/", [item["path"] for item in data["resources"]])
        sdk_status = {item["language"]: item["status"] for item in data["sdk_status"]}
        self.assertEqual(sdk_status["python"], "ready")
        self.assertEqual(sdk_status["javascript"], "ready")
        self.assertEqual(sdk_status["java"], "ready")
        self.assertEqual(sdk_status["csharp"], "ready")
        self.assertEqual(data["spec_url"], "/api/v1/docs/openapi.yaml")

    def test_openapi_spec_returns_public_yaml(self):
        response = self.client.get(reverse("openapi-spec"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.content.decode("utf-8")
        self.assertIn("openapi: 3.1.0", body)
        self.assertIn("IdentityCore Public API", body)
        self.assertIn("/uploads/", body)
        self.assertIn("/organization/me/", body)
        self.assertIn("/api-clients/", body)
        self.assertIn("/verifications/manual-reviews", body)
