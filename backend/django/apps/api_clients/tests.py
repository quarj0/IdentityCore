from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient, APIClientStatus
from apps.organizations.models import Organization, OrganizationStatus
from apps.tenants.models import Tenant


class APIClientModelTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme",
            slug="acme",
            status=OrganizationStatus.ACTIVE,
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )

    def test_generates_prefixed_public_and_client_ids(self):
        api_client = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Backend",
            scopes_json=["verifications:create"],
        )
        api_client.set_client_secret("secret")
        api_client.save()

        self.assertTrue(api_client.public_id.startswith("api_"))
        self.assertTrue(api_client.client_id.startswith("cli_"))

    def test_secret_is_hashed_and_verified(self):
        api_client = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Backend",
            scopes_json=["verifications:create"],
        )
        api_client.set_client_secret("super-secret")
        api_client.save()

        self.assertNotEqual(api_client.client_secret_hash, "super-secret")
        self.assertTrue(api_client.verify_client_secret("super-secret"))


class APIClientEndpointTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme",
            slug="acme",
            status=OrganizationStatus.ACTIVE,
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        access = login_response.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_create_api_client_returns_secret_once(self):
        response = self.client.post(
            reverse("api-client-list-create"),
            {
                "name": "Production Backend",
                "scopes": ["verifications:create", "verifications:read"],
                "allowed_networks": ["197.251.0.15/32"],
                "rate_limit_per_minute": 100,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("client_secret", response.data["data"])
        self.assertEqual(response.data["data"]["scopes"], ["verifications:create", "verifications:read"])

    def test_list_api_clients_is_tenant_scoped(self):
        own_client = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Own Client",
            scopes_json=["verifications:read"],
        )
        own_client.set_client_secret("own-secret")
        own_client.save()

        other_org = Organization.objects.create(name="Beta", slug="beta")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Beta Tenant",
            slug="beta-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        other_client = APIClient(
            tenant=other_tenant,
            created_by=other_user,
            name="Other Client",
            scopes_json=["verifications:read"],
        )
        other_client.set_client_secret("other-secret")
        other_client.save()

        response = self.client.get(reverse("api-client-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["data"]["results"]]
        self.assertEqual(names, ["Own Client"])

    def test_platform_admin_without_tenant_cannot_manage_api_clients(self):
        self.client.credentials()
        admin_user = PlatformUser.objects.create_user(
            email="platform-admin@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            is_platform_admin=True,
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": "platform-admin@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        access = login_response.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(reverse("api-client-list-create"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_api_client_requires_approved_organization(self):
        self.organization.status = OrganizationStatus.PENDING_REVIEW
        self.organization.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            reverse("api-client-list-create"),
            {
                "name": "Production Backend",
                "scopes": ["verifications:create", "verifications:read"],
                "allowed_networks": ["197.251.0.15/32"],
                "rate_limit_per_minute": 100,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("platform approval", response.data["error"]["details"]["detail"][0])
