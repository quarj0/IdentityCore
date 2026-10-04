"""Real PostgreSQL regression: declarations and activation share tenant/provider locks."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Event
from unittest import skipUnless
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.test import TransactionTestCase

from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderAssignment,
    ProviderRoute,
    ProviderRouteStep,
)
from apps.providers.services import publish_provider_route
from apps.providers.test_manifests import document_manifest
from apps.tenants.models import Tenant


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks required")
class ManifestActivationRaceTests(TransactionTestCase):
    def setUp(self):
        org = Organization.objects.create(name="Race", slug="manifest-race")
        self.tenant = Tenant.objects.create(
            organization=org, name="Race", slug="manifest-race"
        )
        manifest = document_manifest()
        manifest["environments"] = ["sandbox", "production"]
        manifest["capabilities"]["document_ocr"]["countries"] = ["*"]
        manifest["capabilities"]["document_ocr"]["document_types"] = ["*"]
        self.provider = Provider.objects.create(
            tenant=self.tenant,
            name="Race",
            code="manifest-race",
            provider_type="document",
            manifest_json=manifest,
        )

    def race(self, activate):
        validated = Event()
        release = Event()
        attempted = Event()
        original = Provider.clean

        def clean(instance):
            original(instance)
            if instance.manifest_json["capabilities"]["document_ocr"]["countries"] == [
                "US"
            ]:
                validated.set()
                if not release.wait(10):
                    raise RuntimeError("Race fixture timed out")

        def edit():
            try:
                provider = Provider.objects.get(pk=self.provider.pk)
                provider.manifest_json = deepcopy(provider.manifest_json)
                provider.manifest_json["capabilities"]["document_ocr"]["countries"] = [
                    "US"
                ]
                provider.save()
            finally:
                connections.close_all()

        def activation():
            attempted.set()
            try:
                activate()
                return "activated"
            except ValidationError:
                return "rejected"
            finally:
                connections.close_all()

        with patch.object(Provider, "clean", clean), ThreadPoolExecutor(
            max_workers=2
        ) as pool:
            edit_future = pool.submit(edit)
            try:
                self.assertTrue(validated.wait(10))
                activation_future = pool.submit(activation)
                self.assertTrue(attempted.wait(10))
                self.assertFalse(activation_future.done())
            finally:
                release.set()
            edit_future.result(timeout=10)
            self.assertEqual(activation_future.result(timeout=10), "rejected")
        self.provider.refresh_from_db()
        self.assertEqual(
            self.provider.manifest_json["capabilities"]["document_ocr"]["countries"],
            ["US"],
        )

    def test_assignment_waits_for_manifest_edit_and_revalidates(self):
        self.race(
            lambda: ProviderAssignment.objects.create(
                tenant=self.tenant,
                provider=self.provider,
                assignment_key="document_ocr",
            )
        )
        self.assertFalse(ProviderAssignment.objects.filter(status="active").exists())

    def test_route_publication_waits_for_manifest_edit_and_revalidates(self):
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="race",
            name="Race",
            environment="sandbox",
            capability="document_ocr",
            country_codes_json=["GH"],
            document_type_ids_json=["passport"],
        )
        ProviderRouteStep.objects.create(
            route=route, provider=self.provider, position=1
        )
        self.race(lambda: publish_provider_route(route))
        route.refresh_from_db()
        self.assertEqual(route.status, "draft")
