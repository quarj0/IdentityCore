from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.access_control.models import Role, RoleScope, UserRole
from apps.accounts.models import EmailVerificationToken
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.accounts.verification import (
    build_email_verification_url,
    issue_and_queue_email_verification,
    verify_email_token,
)
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class PlatformUserModelTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )

    def test_platform_admin_without_tenant_is_valid(self):
        user = PlatformUser.objects.create_user(
            email="admin@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            is_platform_admin=True,
        )

        self.assertIsNone(user.tenant)
        self.assertTrue(user.public_id.startswith("usr_"))
        self.assertEqual(len(user.public_id.split("_", maxsplit=1)[1]), 26)

    def test_non_platform_admin_without_tenant_is_rejected(self):
        with self.assertRaisesMessage(Exception, "Non-platform admin users must belong to a tenant."):
            PlatformUser.objects.create_user(
                email="user@example.com",
                password="StrongPassword123!",
                status=PlatformUserStatus.ACTIVE,
            )

    def test_duplicate_email_is_rejected(self):
        PlatformUser.objects.create_user(
            email="user@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )

        with self.assertRaises(Exception):
            PlatformUser.objects.create_user(
                email="user@example.com",
                password="StrongPassword123!",
                status=PlatformUserStatus.ACTIVE,
                tenant=self.tenant,
            )


class AuthEndpointTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.role = Role.objects.create(
            tenant=self.tenant,
            name="Organization Administrator",
            description="Can manage the tenant account.",
            scope=RoleScope.TENANT,
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="user@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
            first_name="Ama",
            last_name="Mensah",
        )
        UserRole.objects.create(user=self.user, role=self.role, tenant=self.tenant)

    def test_valid_login_returns_tokens_and_user_payload(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertEqual(response.data["data"]["user"]["roles"], [self.role.name])

    def test_invalid_login_is_rejected(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "wrong"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_inactive_user_cannot_log_in(self):
        self.user.status = PlatformUserStatus.INACTIVE
        self.user.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_suspended_user_cannot_log_in(self):
        self.user.status = PlatformUserStatus.SUSPENDED
        self.user.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_locked_user_cannot_log_in(self):
        self.user.status = PlatformUserStatus.LOCKED
        self.user.save(update_fields=["status", "updated_at"])
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_returns_access_token(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        refresh = login_response.data["data"]["tokens"]["refresh"]

        response = self.client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"]["tokens"])

    def test_authenticated_me_returns_user_context(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        access = login_response.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["user"]["tenant_public_id"], self.tenant.public_id)


class EmailVerificationTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="pending_review",
        )
        self.user = PlatformUser.objects.create_user(
            email="pending@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.INACTIVE,
            tenant=self.tenant,
            first_name="Pending",
            last_name="User",
        )

    def test_issue_and_queue_email_verification_creates_token_and_notification(self):
        token, raw_token = issue_and_queue_email_verification(user=self.user)

        self.assertTrue(token.public_id.startswith("evt_"))
        self.assertTrue(raw_token)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user.email,
                template_code="account.email_verification",
            ).exists()
        )
        self.assertIn("token=", build_email_verification_url(raw_token))

    def test_verify_email_token_marks_token_used_and_activates_user(self):
        token, raw_token = issue_and_queue_email_verification(user=self.user)

        verified_user = verify_email_token(raw_token)

        token.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(verified_user.public_id, self.user.public_id)
        self.assertIsNotNone(token.used_at)
        self.assertEqual(self.user.status, PlatformUserStatus.ACTIVE)

    def test_verify_email_token_rejects_expired_token(self):
        token, raw_token = issue_and_queue_email_verification(user=self.user)
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at", "updated_at"])

        with self.assertRaisesMessage(ValueError, "expired"):
            verify_email_token(raw_token)

    def test_issuing_new_token_revokes_previous_token(self):
        first_token, _ = issue_and_queue_email_verification(user=self.user)

        second_token, second_raw_token = issue_and_queue_email_verification(
            user=self.user
        )

        first_token.refresh_from_db()
        self.assertIsNotNone(first_token.revoked_at)
        self.assertIsNone(second_token.revoked_at)
        self.assertEqual(verify_email_token(second_raw_token).public_id, self.user.public_id)
        self.assertEqual(
            EmailVerificationToken.objects.filter(user=self.user).count(),
            2,
        )
