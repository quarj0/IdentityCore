import hashlib
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from apps.access_control.models import Role, RoleScope
from apps.accounts.models import (
    PlatformUser,
    PlatformUserStatus,
    TeamInvitation,
)
from apps.accounts.views import LoginView, TeamInvitationAcceptView
from apps.organizations.models import Organization
from apps.reviewers.models import PlatformAdminInvitation
from apps.tenants.models import Tenant
from common.throttling import SensitivePublicRateThrottle


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {"sensitive_public": "20/min"},
        "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    }
)
class AntiEnumerationTests(APITestCase):
    def setUp(self):
        cache.clear()
        organization = Organization.objects.create(
            name="Enumeration Test", slug="enumeration-test"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Enumeration Tenant",
            slug="enumeration-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="known@example.com",
            password="StrongPassword123!",
            tenant=self.tenant,
            status=PlatformUserStatus.ACTIVE,
        )
        self.role = Role.objects.create(
            tenant=self.tenant,
            name="Member",
            scope=RoleScope.TENANT,
            status="active",
        )
        self.platform_admin = PlatformUser.objects.create_user(
            email="platform-known@example.com",
            password="StrongPassword123!",
            is_platform_admin=True,
            status=PlatformUserStatus.ACTIVE,
        )

    def test_login_response_does_not_distinguish_unknown_email(self):
        wrong_password = self.client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": "incorrect"},
            format="json",
        )
        unknown_email = self.client.post(
            reverse("auth-login"),
            {"email": "unknown@example.com", "password": "incorrect"},
            format="json",
        )

        self.assertEqual(wrong_password.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unknown_email.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            wrong_password.data["error"]["message"],
            unknown_email.data["error"]["message"],
        )

    def test_password_reset_response_does_not_reveal_account_existence(self):
        mutation = """
            mutation PasswordReset($email: String!) {
              requestPasswordReset(email: $email) { ok message nextAction }
            }
        """
        known = self.client.post(
            "/api/graphql",
            {"query": mutation, "variables": {"email": self.user.email}},
            format="json",
        )
        unknown = self.client.post(
            "/api/graphql",
            {"query": mutation, "variables": {"email": "unknown@example.com"}},
            format="json",
        )

        self.assertEqual(known.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(
            known.json()["data"]["requestPasswordReset"],
            unknown.json()["data"]["requestPasswordReset"],
        )

    def test_invitation_acceptance_uses_one_public_rejection(self):
        raw_token = "existing-account-invitation"
        TeamInvitation.objects.create(
            tenant=self.tenant,
            email=self.user.email,
            role=self.role,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(days=1),
            invited_by=self.user,
        )
        existing_account = self.client.post(
            "/api/v1/auth/team/invitations/accept",
            {"token": raw_token, "password": "AnotherStrongPassword123!"},
            format="json",
        )
        invalid_token = self.client.post(
            "/api/v1/auth/team/invitations/accept",
            {"token": "unknown-token", "password": "AnotherStrongPassword123!"},
            format="json",
        )

        self.assertEqual(existing_account.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_token.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            existing_account.data["data"]["detail"],
            invalid_token.data["data"]["detail"],
        )

    def test_platform_invitation_uses_one_public_rejection(self):
        role = Role.objects.create(
            name="Platform Operator",
            scope=RoleScope.PLATFORM,
            status="active",
        )
        invitation = PlatformAdminInvitation.objects.create(
            email=self.platform_admin.email,
            role=role,
            invited_by=self.platform_admin,
            expires_at=timezone.now() + timedelta(days=1),
        )
        raw_token = "existing-platform-account-invitation"
        invitation.set_token(raw_token)
        invitation.save(update_fields=["token_hash", "updated_at"])
        mutation = """
            mutation AcceptInvitation($token: String!, $password: String!) {
              acceptPlatformAdminInvitation(token: $token, password: $password) {
                user { publicId }
              }
            }
        """
        existing_account = self.client.post(
            "/api/graphql",
            {
                "query": mutation,
                "variables": {
                    "token": raw_token,
                    "password": "AnotherStrongPassword123!",
                },
            },
            format="json",
        )
        invalid_token = self.client.post(
            "/api/graphql",
            {
                "query": mutation,
                "variables": {
                    "token": "unknown-token",
                    "password": "AnotherStrongPassword123!",
                },
            },
            format="json",
        )

        self.assertEqual(existing_account.status_code, status.HTTP_200_OK)
        self.assertEqual(invalid_token.status_code, status.HTTP_200_OK)
        self.assertEqual(
            existing_account.json()["errors"][0]["message"],
            invalid_token.json()["errors"][0]["message"],
        )

    def test_public_throttle_key_is_independent_of_claimed_identity(self):
        factory = APIRequestFactory()
        known = factory.post(
            "/api/v1/auth/login",
            {"email": self.user.email},
            REMOTE_ADDR="192.0.2.10",
        )
        unknown = factory.post(
            "/api/v1/auth/login",
            {"email": "unknown@example.com"},
            REMOTE_ADDR="192.0.2.10",
        )
        throttle = SensitivePublicRateThrottle()

        self.assertEqual(
            throttle.get_cache_key(known, LoginView()),
            throttle.get_cache_key(unknown, LoginView()),
        )
        self.assertEqual(LoginView.throttle_classes, [SensitivePublicRateThrottle])
        self.assertEqual(
            TeamInvitationAcceptView.throttle_classes,
            [SensitivePublicRateThrottle],
        )

    def test_public_throttle_ignores_untrusted_forwarded_address(self):
        factory = APIRequestFactory()
        first = factory.post(
            "/api/v1/auth/login",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.1",
        )
        second = factory.post(
            "/api/v1/auth/login",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="203.0.113.2",
        )
        throttle = SensitivePublicRateThrottle()

        self.assertEqual(
            throttle.get_cache_key(first, LoginView()),
            throttle.get_cache_key(second, LoginView()),
        )

    @patch.object(SensitivePublicRateThrottle, "get_rate", return_value="20/min")
    def test_known_and_unknown_login_attempts_reach_the_same_rate_limit(
        self, _mock_rate
    ):
        known = None
        for _ in range(21):
            known = self.client.post(
                reverse("auth-login"),
                {"email": self.user.email, "password": "incorrect"},
                format="json",
                REMOTE_ADDR="192.0.2.20",
            )

        cache.clear()
        unknown = None
        for _ in range(21):
            unknown = self.client.post(
                reverse("auth-login"),
                {"email": "unknown@example.com", "password": "incorrect"},
                format="json",
                REMOTE_ADDR="192.0.2.20",
            )

        self.assertEqual(known.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(unknown.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(known.data["error"]["code"], unknown.data["error"]["code"])
