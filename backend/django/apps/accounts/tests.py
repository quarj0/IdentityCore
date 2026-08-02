from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.access_control.models import Role, RoleScope, UserRole
from apps.accounts.models import EmailVerificationToken
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.accounts.verification import (
    build_email_verification_url,
    issue_and_queue_email_verification,
    verify_email_token,
)
from apps.accounts.mfa import totp
from apps.audit.models import AuditEvent
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
        with self.assertRaisesMessage(
            Exception, "Non-platform admin users must belong to a tenant."
        ):
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
        self.assertNotIn("refresh", response.data["data"]["tokens"])
        self.assertIn("identitycore_refresh", response.cookies)
        self.assertTrue(response.cookies["identitycore_refresh"]["httponly"])
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
        first_cookie = login_response.cookies["identitycore_refresh"].value
        response = self.client.post(reverse("auth-refresh"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertNotEqual(
            response.cookies["identitycore_refresh"].value,
            first_cookie,
        )

    def test_refresh_sessions_are_isolated_by_first_party_app(self):
        dashboard_login = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
            HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard",
        )
        platform_login = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
            HTTP_X_IDENTITYCORE_SESSION_SCOPE="platform_admin",
        )

        self.assertIn("identitycore_refresh_dashboard", dashboard_login.cookies)
        self.assertIn("identitycore_refresh_platform_admin", platform_login.cookies)

        dashboard_refresh = self.client.post(
            reverse("auth-refresh"),
            {},
            format="json",
            HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard",
        )
        platform_refresh = self.client.post(
            reverse("auth-refresh"),
            {},
            format="json",
            HTTP_X_IDENTITYCORE_SESSION_SCOPE="platform_admin",
        )

        self.assertEqual(dashboard_refresh.status_code, status.HTTP_200_OK)
        self.assertEqual(platform_refresh.status_code, status.HTTP_200_OK)

    def test_refresh_rejects_untrusted_cookie_origin(self):
        self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        response = self.client.post(
            reverse("auth-refresh"),
            {},
            format="json",
            HTTP_ORIGIN="https://attacker.example",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_blacklisted_refresh_returns_401_and_clears_cookie(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        raw_token = login_response.cookies["identitycore_refresh"].value
        RefreshToken(raw_token).blacklist()
        response = self.client.post(reverse("auth-refresh"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "authentication_failed")
        self.assertEqual(response.cookies["identitycore_refresh"].value, "")

    def test_logout_revokes_and_clears_refresh_cookie(self):
        self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        response = self.client.post(reverse("auth-logout"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies["identitycore_refresh"].value, "")

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
        self.assertEqual(
            response.data["data"]["user"]["tenant_public_id"], self.tenant.public_id
        )

    def test_authenticated_team_returns_tenant_members(self):
        PlatformUser.objects.create_user(
            email="reviewer@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        access = login_response.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(reverse("auth-team"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {item["email"] for item in response.data["data"]["results"]}
        self.assertEqual(emails, {"user@example.com", "reviewer@example.com"})


class MFAEndpointTests(APITestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Privileged Org",
            slug="privileged-org",
            settings_json={"privileged_mfa_roles": ["Organization Administrator"]},
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Privileged Tenant",
            slug="privileged-tenant",
            status="active",
        )
        role = Role.objects.create(
            tenant=self.tenant,
            name="Organization Administrator",
            scope=RoleScope.TENANT,
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="privileged@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        UserRole.objects.create(user=self.user, role=role, tenant=self.tenant)

    def login(self):
        return self.client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": "StrongPassword123!"},
            format="json",
        )

    def enroll(self):
        login = self.login()
        token = login.data["data"]["mfa_token"]
        enrollment = self.client.post(
            reverse("auth-mfa-enroll"), {"mfa_token": token}, format="json"
        )
        secret = enrollment.data["data"]["secret"]
        confirmed = self.client.post(
            reverse("auth-mfa-enroll-confirm"),
            {"mfa_token": token, "code": totp(secret)},
            format="json",
        )
        return secret, confirmed

    def test_privileged_login_cannot_bypass_enrollment(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data["data"]["mfa_enrollment_required"])
        self.assertNotIn("tokens", response.data["data"])
        self.assertNotIn("identitycore_refresh", response.cookies)

    def test_legacy_refresh_token_cannot_bypass_mfa_policy(self):
        self.client.cookies["identitycore_refresh"] = str(
            RefreshToken.for_user(self.user)
        )
        response = self.client.post(reverse("auth-refresh"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.cookies["identitycore_refresh"].value, "")

    def test_enrollment_challenge_recovery_and_replay_protection(self):
        secret, confirmed = self.enroll()
        self.assertEqual(confirmed.status_code, status.HTTP_200_OK)
        self.assertIn("access", confirmed.data["data"]["tokens"])
        recovery = confirmed.data["data"]["recovery_codes"][0]
        self.assertEqual(len(confirmed.data["data"]["recovery_codes"]), 10)

        login = self.login()
        self.assertFalse(login.data["data"]["mfa_enrollment_required"])
        challenged = self.client.post(
            reverse("auth-mfa-challenge"),
            {"mfa_token": login.data["data"]["mfa_token"], "code": totp(secret)},
            format="json",
        )
        self.assertEqual(challenged.status_code, status.HTTP_200_OK)
        challenge_replay = self.client.post(
            reverse("auth-mfa-challenge"),
            {"mfa_token": login.data["data"]["mfa_token"], "code": totp(secret)},
            format="json",
        )
        self.assertEqual(challenge_replay.status_code, status.HTTP_401_UNAUTHORIZED)

        login = self.login()
        recovered = self.client.post(
            reverse("auth-mfa-challenge"),
            {"mfa_token": login.data["data"]["mfa_token"], "code": recovery},
            format="json",
        )
        self.assertEqual(recovered.status_code, status.HTTP_200_OK)
        replay = self.client.post(
            reverse("auth-mfa-challenge"),
            {"mfa_token": login.data["data"]["mfa_token"], "code": recovery},
            format="json",
        )
        self.assertEqual(replay.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            AuditEvent.objects.filter(action="user.mfa_challenge_failed").exists()
        )

    def test_authenticated_reset_requires_password_and_second_factor(self):
        secret, confirmed = self.enroll()
        access = confirmed.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        rejected = self.client.post(
            reverse("auth-mfa-reset"),
            {"password": "wrong", "code": totp(secret)},
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(
            reverse("auth-mfa-reset"),
            {"password": "StrongPassword123!", "code": totp(secret)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.mfa_enabled)
        self.assertTrue(AuditEvent.objects.filter(action="user.mfa_reset").exists())


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

    def test_verify_email_token_is_idempotent_after_success(self):
        _, raw_token = issue_and_queue_email_verification(user=self.user)

        first_user = verify_email_token(raw_token)
        second_user = verify_email_token(raw_token)

        self.assertEqual(second_user.public_id, first_user.public_id)

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
        self.assertEqual(
            verify_email_token(second_raw_token).public_id, self.user.public_id
        )
        self.assertEqual(
            EmailVerificationToken.objects.filter(user=self.user).count(),
            2,
        )
