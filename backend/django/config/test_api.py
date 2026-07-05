from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CatalogEndpointTests(APITestCase):
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
