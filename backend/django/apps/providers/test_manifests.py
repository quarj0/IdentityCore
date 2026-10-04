from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

User = get_user_model()
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderAssignment,
    ProviderRoute,
    ProviderRouteStep,
)
from apps.providers.manifests import validate_manifest
from apps.providers.services import publish_provider_route
from apps.tenants.models import Tenant


def document_manifest():
    return {
        "manifest_version": "1",
        "contract_version": "1",
        "capabilities": {
            "document_ocr": {
                "countries": ["GH"],
                "document_types": ["passport"],
                "input_schema": "document_ocr.input/v1",
                "output_schema": "document_ocr.output/v1",
            }
        },
        "environments": ["sandbox"],
        "residency": ["GH"],
        "retention_days": 0,
        "processor": "Synthetic processor",
        "transfer_notes": "No onward transfers",
    }


class ManifestTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(name="One", slug="one")
        self.tenant = Tenant.objects.create(
            organization=organization, name="One", slug="one"
        )
        self.provider = Provider.objects.create(
            tenant=self.tenant,
            name="One",
            code="one",
            provider_type="document",
            manifest_json=document_manifest(),
            configuration_json={"secret": "private-credential"},
        )

    def test_validation_versions_types_unknown_keys_and_bounds(self):
        for key, value in (
            ("contract_version", "2"),
            ("retention_days", True),
            ("residency", []),
            ("environments", ["unknown"]),
        ):
            manifest = document_manifest()
            manifest[key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                validate_manifest(manifest, provider_type="document")
        manifest = document_manifest()
        manifest["secret"] = "forbidden"
        with self.assertRaises(ValidationError):
            validate_manifest(manifest, provider_type="document")
        with self.assertRaises(ValidationError):
            validate_manifest(document_manifest(), provider_type="risk")

    def test_assignment_rejects_missing_capability_and_partial_coverage(self):
        for capability in ("document_quality", "document_ocr"):
            with self.subTest(capability=capability), self.assertRaises(
                ValidationError
            ):
                ProviderAssignment.objects.create(
                    tenant=self.tenant,
                    provider=self.provider,
                    assignment_key=capability,
                )

    def test_publication_checks_environment_and_coverage(self):
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="ocr",
            name="OCR",
            environment="production",
            capability="document_ocr",
            country_codes_json=["GH"],
            document_type_ids_json=["passport"],
        )
        ProviderRouteStep.objects.create(
            route=route, provider=self.provider, position=1
        )
        with self.assertRaises(ValidationError):
            publish_provider_route(route)
        route.environment = "sandbox"
        route.country_codes_json = ["US"]
        route.save()
        with self.assertRaises(ValidationError):
            publish_provider_route(route)
        route.country_codes_json = ["GH"]
        route.save()
        self.assertEqual(publish_provider_route(route).status, "active")
        self.provider.manifest_json["environments"] = ["production"]
        with self.assertRaises(ValidationError):
            self.provider.save()

    def test_global_assignment_requires_both_environments(self):
        self.provider.manifest_json["capabilities"]["document_ocr"]["countries"] = ["*"]
        self.provider.manifest_json["capabilities"]["document_ocr"][
            "document_types"
        ] = ["*"]
        self.provider.save()
        with self.assertRaises(ValidationError):
            ProviderAssignment.objects.create(
                tenant=self.tenant,
                provider=self.provider,
                assignment_key="document_ocr",
            )
        self.provider.manifest_json["environments"] = ["sandbox", "production"]
        self.provider.save()
        ProviderAssignment.objects.create(
            tenant=self.tenant, provider=self.provider, assignment_key="document_ocr"
        )
        self.provider.manifest_json["environments"] = ["sandbox"]
        with self.assertRaises(ValidationError):
            self.provider.save()

    def test_tenant_listing_hides_foreign_providers_and_all_configuration(self):
        other_org = Organization.objects.create(name="Two", slug="two")
        other = Tenant.objects.create(organization=other_org, name="Two", slug="two")
        Provider.objects.create(
            tenant=other,
            name="Foreign",
            code="foreign",
            provider_type="risk",
            configuration_json={"api_key": "foreign-secret"},
        )
        platform = Provider.objects.create(
            name="Platform",
            code="platform",
            provider_type="document",
            configuration_json={"token": "platform-secret"},
        )
        user = User.objects.create_user(
            email="one@example.test", password="unused", tenant=self.tenant
        )
        client = APIClient()
        client.force_authenticate(user=user)
        from django.urls import reverse

        response = client.get(reverse("provider-list"))
        self.assertEqual(response.status_code, 200)
        text = str(response.data)
        for value in (
            "private-credential",
            "foreign-secret",
            "platform-secret",
            "Foreign",
        ):
            self.assertNotIn(value, text)
        self.assertIn(platform.public_id, text)
        self.assertIn(self.provider.public_id, text)
