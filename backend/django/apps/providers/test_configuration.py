from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient

from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.organizations.models import Organization
from apps.providers.configuration import (
    activate_configuration,
    assign_configuration,
    create_configuration,
    invoke_configured_provider,
    serialize_configuration,
    test_configuration,
)
from apps.providers.http_adapter import SecureHTTPAdapterError
from apps.providers.models import Provider
from apps.providers.test_manifests import document_manifest
from apps.providers.serializers import serialize_provider
from apps.providers.services import (
    invoke_selected_provider_operation,
    resolve_provider_chain,
)
from apps.tenants.models import Tenant


class ConfigurationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Setup", slug="setup", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=self.org, name="Setup", slug="setup", status="active"
        )
        User = get_user_model()
        self.requester = User.objects.create_user(
            email="requester@example.test", password="unused", tenant=self.tenant
        )
        self.approver = User.objects.create_user(
            email="approver@example.test", password="unused", tenant=self.tenant
        )
        role = Role.objects.create(
            tenant=self.tenant, scope="tenant", name="Provider manager"
        )
        for code in ("manage_providers", "approve_provider_promotion"):
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": code}
            )
            RolePermission.objects.create(role=role, permission=permission)
        for user in (self.requester, self.approver):
            UserRole.objects.create(user=user, role=role, tenant=self.tenant)
        manifest = document_manifest()
        manifest["environments"] = ["sandbox", "production"]
        self.provider = Provider.objects.create(
            tenant=self.tenant,
            name="Test",
            code="setup-test",
            provider_type="document",
            manifest_json=manifest,
        )
        self.public = {
            "endpoint_url": "https://provider.example.test/invoke",
            "allowed_hosts": ["provider.example.test"],
            "timeout_seconds": 10,
        }
        self.credentials = {"api_key": "separate-sandbox-credential"}

    def create(self, **overrides):
        return create_configuration(
            provider=self.provider,
            user=self.requester,
            environment="sandbox",
            public_configuration=self.public,
            credentials=self.credentials,
            **overrides
        )

    def connection_checked(self, config):
        def reply(**kwargs):
            payload = kwargs["payload"]
            self.assertNotIn("credentials", payload)
            self.assertEqual(
                kwargs["headers"]["Authorization"],
                "Bearer " + config.credentials_json["api_key"],
            )
            return {
                "status": "completed",
                "contract_version": "1",
                "challenge": payload["challenge"],
                "capabilities": payload["capabilities"],
            }

        with patch(
            "apps.providers.configuration.SecureHTTPProviderAdapter.post_json",
            side_effect=reply,
        ):
            return test_configuration(config=config, user=self.requester)

    def sandbox(self):
        return activate_configuration(
            config=self.connection_checked(self.create()), user=self.requester
        )

    def test_secret_is_encrypted_and_never_serialized(self):
        config = self.create()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT credentials_json FROM providers_providerenvironmentconfiguration WHERE id = %s",
                [config.id],
            )
            raw = str(cursor.fetchone()[0])
        self.assertNotIn(self.credentials["api_key"], raw)
        self.assertNotIn(
            self.credentials["api_key"], str(serialize_configuration(config))
        )
        self.assertIn("__enc__", raw)
        config.public_configuration_json = {**self.public, "timeout_seconds": 12}
        with self.assertRaises(ValidationError):
            config.save()

    def test_exact_challenge_failed_test_and_freshness(self):
        config = self.create()
        with patch(
            "apps.providers.configuration.SecureHTTPProviderAdapter.post_json",
            return_value={
                "status": "completed",
                "contract_version": "1",
                "challenge": "wrong",
                "capabilities": ["document_ocr"],
            },
        ):
            config = test_configuration(config=config, user=self.requester)
        self.assertFalse(config.test_succeeded)
        with self.assertRaises(ValidationError):
            activate_configuration(config=config, user=self.requester)
        config = self.connection_checked(config)
        config.tested_at = timezone.now() - timedelta(minutes=16)
        config.save(update_fields=["tested_at"])
        with self.assertRaises(ValidationError):
            activate_configuration(config=config, user=self.requester)
        self.assertEqual(
            self.tenant.audit_events.filter(
                action="provider.connection_tested"
            ).count(),
            2,
        )

    def test_promotion_separate_credentials_independent_approval_and_new_test(self):
        sandbox = self.sandbox()
        self.assertTrue(
            serialize_provider(self.provider)["configuration"]["configured"]
        )
        with self.assertRaises(ValidationError):
            create_configuration(
                provider=self.provider,
                user=self.requester,
                environment="production",
                public_configuration=self.public,
                credentials=self.credentials,
                source=sandbox,
            )
        production = create_configuration(
            provider=self.provider,
            user=self.requester,
            environment="production",
            public_configuration={
                **self.public,
                "endpoint_url": "https://provider.example.test/production",
            },
            credentials={"api_key": "separate-production-credential"},
            source=sandbox,
        )
        self.assertFalse(production.test_succeeded)
        self.assertEqual(
            production.diff_json["endpoint_url"]["before"], self.public["endpoint_url"]
        )
        self.assertNotIn("credential", str(production.diff_json))
        with self.assertRaises(ValidationError):
            activate_configuration(config=production, user=self.approver)
        production = self.connection_checked(production)
        with self.assertRaises(ValidationError):
            activate_configuration(config=production, user=self.requester)
        production = activate_configuration(config=production, user=self.approver)
        self.assertEqual(production.approved_by_id, self.approver.pk)
        route = assign_configuration(
            config=production,
            user=self.requester,
            capability="document_ocr",
            countries=["GH"],
            document_types=["passport"],
        )
        self.assertEqual(route.environment, "production")
        self.assertEqual(
            resolve_provider_chain(
                tenant=self.tenant,
                environment="production",
                check_type="document_ocr",
                country_code="GH",
                document_type="passport",
            ).providers,
            (self.provider,),
        )

    def test_runtime_never_falls_back_to_sandbox_configuration(self):
        self.sandbox()
        with self.assertRaises(SecureHTTPAdapterError):
            invoke_configured_provider(
                provider=self.provider,
                environment="production",
                capability="document_ocr",
                inputs={},
                timeout_seconds=30,
            )
        with patch(
            "apps.providers.configuration.SecureHTTPProviderAdapter.post_json",
            return_value={
                "status": "completed",
                "contract_version": "1",
                "capability": "document_ocr",
            },
        ) as post:
            invoke_selected_provider_operation(
                provider=self.provider,
                environment="sandbox",
                check_type="document_ocr",
                timeout_seconds=5,
                operation_kwargs={"fixture": True},
                built_in_operation=lambda: None,
            )
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"],
            "Bearer " + self.credentials["api_key"],
        )
        self.assertEqual(post.call_args.kwargs["payload"]["environment"], "sandbox")

    def test_changed_manifest_invalidates_test_and_production_approval(self):
        config = self.connection_checked(self.create())
        self.provider.manifest_json["retention_days"] = 1
        self.provider.save()
        with self.assertRaises(ValidationError):
            activate_configuration(config=config, user=self.requester)

    def test_cross_tenant_and_unprivileged_api_access(self):
        client = APIClient()
        client.force_authenticate(user=self.requester)
        config = self.create()
        url = reverse(
            "provider-configuration-list",
            kwargs={"provider_id": self.provider.public_id},
        )
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.credentials["api_key"], str(response.data))
        other_org = Organization.objects.create(name="Other", slug="other")
        other = Tenant.objects.create(
            organization=other_org, name="Other", slug="other"
        )
        foreign = Provider.objects.create(
            tenant=other, name="Foreign", code="foreign-setup", provider_type="risk"
        )
        self.assertEqual(
            client.get(
                reverse(
                    "provider-configuration-list",
                    kwargs={"provider_id": foreign.public_id},
                )
            ).status_code,
            404,
        )
        self.requester.user_roles.all().delete()
        self.assertEqual(client.get(url).status_code, 403)
        action = reverse(
            "provider-configuration-action",
            kwargs={"configuration_id": config.public_id, "action": "test"},
        )
        self.assertEqual(client.post(action, {}, format="json").status_code, 403)

    def test_unsafe_endpoints_credentials_and_pending_production_are_rejected(self):
        for endpoint in (
            "http://provider.example.test",
            "https://provider.example.test/?token=secret",
            "https://other.test/invoke",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(
                (ValidationError, SecureHTTPAdapterError)
            ):
                create_configuration(
                    provider=self.provider,
                    user=self.requester,
                    environment="sandbox",
                    public_configuration={**self.public, "endpoint_url": endpoint},
                    credentials=self.credentials,
                )
        sandbox = self.sandbox()
        self.org.status = "pending"
        self.org.save()
        with self.assertRaises(ValidationError):
            create_configuration(
                provider=self.provider,
                user=self.requester,
                environment="production",
                public_configuration=self.public,
                credentials=self.credentials,
                source=sandbox,
            )

    def test_retired_sandbox_source_cannot_be_promoted(self):
        source = self.sandbox()
        production = create_configuration(
            provider=self.provider,
            user=self.requester,
            environment="production",
            source=source,
            public_configuration=self.public,
            credentials={"api_key": "separate-production-credential"},
        )
        production = self.connection_checked(production)
        self.sandbox()
        with self.assertRaisesMessage(ValidationError, "active sandbox source"):
            activate_configuration(config=production, user=self.approver)
        production.refresh_from_db()
        self.assertEqual(production.status, "draft")

    def test_unsupported_runtime_cannot_be_assigned(self):
        config = self.sandbox()
        for capability in ("risk_check", "identity_lookup"):
            with self.subTest(capability=capability), self.assertRaisesMessage(
                ValidationError, "supported verification runtime"
            ):
                assign_configuration(
                    config=config, user=self.requester, capability=capability
                )
