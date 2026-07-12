from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent, AuditActorType
from apps.organizations.models import Organization
from apps.providers.models import Provider, ProviderStatus, ProviderType
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.webhooks.models import WebhookEndpoint


class PlatformAdminEndpointTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme-admin")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Admin Tenant",
            slug="acme-admin-tenant",
            status="active",
        )
        self.tenant_user = PlatformUser.objects.create_user(
            email="tenant@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.platform_admin = PlatformUser.objects.create_superuser(
            email="platform-admin@example.com",
            password="StrongPassword123!",
        )

        self.provider = Provider.objects.create(
            name="Internal OCR",
            code="internal-ocr",
            provider_type=ProviderType.DOCUMENT,
            status=ProviderStatus.ACTIVE,
        )
        self.policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            description="Primary policy",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.tenant_user,
        )
        self.api_client = APIClient(
            tenant=self.tenant,
            created_by=self.tenant_user,
            name="Platform Admin Client",
            scopes_json=["verifications:create"],
            allowed_ips_json=[],
            rate_limit_per_minute=60,
        )
        self.api_client.set_client_secret("client-secret")
        self.api_client.save()
        self.webhook_endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            description="Platform admin webhook",
            events_json=["verification.created"],
            created_by=self.tenant_user,
        )
        self.webhook_endpoint.set_secret("webhook-secret")
        self.webhook_endpoint.save()
        self.audit_event = AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type=AuditActorType.PLATFORM_USER,
            actor_id=self.tenant_user.public_id,
            action="onboarding.organization_verification_submitted",
            target_type="organization",
            target_id=self.organization.public_id,
            ip_address="127.0.0.1",
            user_agent="pytest",
            metadata_json={"status": "submitted"},
        )

    def test_platform_admin_endpoints_return_live_data(self):
        self.client.force_authenticate(self.platform_admin)

        provider_response = self.client.get("/api/v1/platform-admin/providers/")
        policy_response = self.client.get("/api/v1/platform-admin/policies/")
        api_client_response = self.client.get("/api/v1/platform-admin/api-clients/")
        webhook_response = self.client.get("/api/v1/platform-admin/webhooks/")
        audit_response = self.client.get("/api/v1/platform-admin/audit-events/")

        self.assertEqual(provider_response.status_code, status.HTTP_200_OK)
        self.assertEqual(policy_response.status_code, status.HTTP_200_OK)
        self.assertEqual(api_client_response.status_code, status.HTTP_200_OK)
        self.assertEqual(webhook_response.status_code, status.HTTP_200_OK)
        self.assertEqual(audit_response.status_code, status.HTTP_200_OK)

        self.assertEqual(provider_response.data["data"]["results"][0]["code"], "internal-ocr")
        self.assertEqual(policy_response.data["data"]["results"][0]["id"], self.policy.public_id)
        self.assertEqual(
            api_client_response.data["data"]["results"][0]["public_id"],
            self.api_client.public_id,
        )
        self.assertEqual(
            webhook_response.data["data"]["results"][0]["id"],
            self.webhook_endpoint.public_id,
        )
        self.assertEqual(
            audit_response.data["data"]["results"][0]["id"],
            self.audit_event.public_id,
        )

    def test_platform_admin_endpoints_require_platform_admin_access(self):
        self.client.force_authenticate(self.tenant_user)

        response = self.client.get("/api/v1/platform-admin/providers/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
