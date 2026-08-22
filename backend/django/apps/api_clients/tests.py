from datetime import timedelta

from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory, APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient, APIIdempotencyRecord
from apps.api_clients.tasks import cleanup_expired_idempotency_records_task
from apps.audit.models import AuditEvent
from common.authentication import APIClientAuthentication
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
            HTTP_IDEMPOTENCY_KEY="create-production-backend",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("client_secret", response.data["data"])
        self.assertEqual(
            response.data["data"]["scopes"],
            ["verifications:create", "verifications:read"],
        )

    def test_create_api_client_requires_idempotency_key(self):
        response = self.client.post(
            reverse("api-client-list-create"),
            {"name": "Missing key", "scopes": ["verifications:read"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("idempotency_key", response.data["error"]["details"])

    def test_create_api_client_replays_secret_for_same_key_and_payload(self):
        payload = {"name": "Replay client", "scopes": ["verifications:read"]}
        first = self.client.post(
            reverse("api-client-list-create"),
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="replay-api-client",
        )
        replay = self.client.post(
            reverse("api-client-list-create"),
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="replay-api-client",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(replay.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["data"], replay.data["data"])
        self.assertEqual(APIClient.objects.filter(name="Replay client").count(), 1)

    def test_create_api_client_rejects_key_reuse_with_different_payload(self):
        url = reverse("api-client-list-create")
        self.client.post(
            url,
            {"name": "First client", "scopes": ["verifications:read"]},
            format="json",
            HTTP_IDEMPOTENCY_KEY="conflicting-api-client",
        )
        conflict = self.client.post(
            url,
            {"name": "Different client", "scopes": ["verifications:read"]},
            format="json",
            HTTP_IDEMPOTENCY_KEY="conflicting-api-client",
        )

        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(APIClient.objects.filter(name="Different client").exists())

    def test_expired_api_client_key_can_be_reused(self):
        url = reverse("api-client-list-create")
        payload = {"name": "Expiring client", "scopes": ["verifications:read"]}
        first = self.client.post(
            url,
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="expired-api-client",
        )
        APIIdempotencyRecord.objects.filter(key="expired-api-client").update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        after_expiry = self.client.post(
            url,
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="expired-api-client",
        )

        self.assertEqual(after_expiry.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(
            first.data["data"]["public_id"], after_expiry.data["data"]["public_id"]
        )
        self.assertEqual(APIClient.objects.filter(name="Expiring client").count(), 2)

    def test_cleanup_task_deletes_only_expired_idempotency_records(self):
        url = reverse("api-client-list-create")
        for key, name in (
            ("expired-record", "Expired record"),
            ("active-record", "Active record"),
        ):
            response = self.client.post(
                url,
                {"name": name, "scopes": ["verifications:read"]},
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        APIIdempotencyRecord.objects.filter(key="expired-record").update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        deleted = cleanup_expired_idempotency_records_task(limit=100)

        self.assertEqual(deleted, 1)
        self.assertFalse(
            APIIdempotencyRecord.objects.filter(key="expired-record").exists()
        )
        self.assertTrue(
            APIIdempotencyRecord.objects.filter(key="active-record").exists()
        )

    @override_settings(API_CLIENT_ROTATION_OVERLAP_SECONDS=60)
    def test_rotate_keeps_old_secret_valid_only_during_overlap(self):
        client = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Rotating Backend",
            scopes_json=["verifications:read"],
        )
        client.set_client_secret("old-secret")
        client.save()

        response = self.client.post(
            reverse(
                "api-client-action",
                kwargs={"client_id": client.public_id, "action": "rotate"},
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rotated_secret = response.data["data"]["client_secret"]
        self.assertNotEqual(rotated_secret, "old-secret")
        self.assertIsNotNone(response.data["data"]["client_secret_overlap_expires_at"])

        client.refresh_from_db()
        self.assertTrue(client.verify_client_secret("old-secret"))
        self.assertTrue(client.verify_client_secret(rotated_secret))
        self.assertNotEqual(client.previous_client_secret_hash, "old-secret")
        self.assertEqual(
            AuditEvent.objects.filter(
                action="api_client.rotate", target_id=client.public_id
            ).count(),
            1,
        )

        request = APIRequestFactory().get(
            "/",
            HTTP_X_CLIENT_ID=client.client_id,
            HTTP_AUTHORIZATION="Bearer old-secret",
        )
        authenticated, authenticated_secret = APIClientAuthentication().authenticate(
            request
        )
        self.assertEqual(authenticated, client)
        self.assertEqual(authenticated_secret, "old-secret")

        client.previous_client_secret_expires_at = timezone.now() - timedelta(seconds=1)
        client.save(update_fields=["previous_client_secret_expires_at", "updated_at"])
        with self.assertRaises(AuthenticationFailed):
            APIClientAuthentication().authenticate(request)
        self.assertTrue(client.verify_client_secret(rotated_secret))

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
        PlatformUser.objects.create_user(
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
            HTTP_IDEMPOTENCY_KEY="pending-org-client",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "platform approval", response.data["error"]["details"]["detail"][0]
        )
