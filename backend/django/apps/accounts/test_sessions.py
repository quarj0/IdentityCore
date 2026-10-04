from datetime import timedelta
from unittest.mock import patch

from django.db import OperationalError
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from apps.accounts.models import DashboardSession, PlatformUser, RefreshTokenSession
from apps.accounts.passwords import change_password
from apps.accounts.sessions import purge_expired_session_history
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class DashboardSessionTests(APITestCase):
    password = "StrongPassword123!"

    def setUp(self):
        organization = Organization.objects.create(
            name="Session tests", slug="session-tests"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Session tests",
            slug="session-tests",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.test",
            password=self.password,
            tenant=self.tenant,
            status="active",
        )

    def login(self, email=None):
        client = APIClient()
        response = client.post(
            "/api/v1/auth/login",
            {"email": email or self.user.email, "password": self.password},
            format="json",
            HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard",
            HTTP_USER_AGENT="Chrome/100 Windows secret-should-not-persist",
            REMOTE_ADDR="192.0.2.123",
        )
        self.assertEqual(response.status_code, 200, response.data)
        access = response.data["data"]["tokens"]["access"]
        client.credentials(
            HTTP_AUTHORIZATION="Bearer " + access,
            HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard",
        )
        token = RefreshToken(response.cookies["identitycore_refresh_dashboard"].value)
        return client, token, access

    def test_listing_owns_and_masks_session_metadata(self):
        client, token, _ = self.login()
        self.login()
        response = client.get("/api/v1/auth/sessions")
        rows = response.data["data"]["results"]
        self.assertEqual(len(rows), 2)
        current = next(row for row in rows if row["current"])
        self.assertEqual(current["id"], token["session_id"])
        self.assertEqual(current["peer_network"], "192.0.2.0/24")
        self.assertEqual(current["device_label"], "Chrome on Windows")
        self.assertNotIn("secret-should-not-persist", str(rows))
        self.assertNotIn(token["jti"], str(rows))
        self.assertNotIn(str(token["family_id"]), str(rows))

    def test_revoked_access_and_refresh_fail_immediately_on_rest_and_graphql(self):
        manager, _, _ = self.login()
        target, token, _ = self.login()
        self.assertEqual(
            manager.post(
                "/api/v1/auth/sessions/" + token["session_id"] + "/revoke"
            ).status_code,
            200,
        )
        self.assertEqual(target.get("/api/v1/auth/me").status_code, 401)
        self.assertEqual(
            target.post(
                "/api/graphql", {"query": "{ me { publicId } }"}, format="json"
            ).status_code,
            401,
        )
        self.assertEqual(target.post("/api/v1/auth/refresh").status_code, 401)
        self.assertEqual(manager.get("/api/v1/auth/me").status_code, 200)

    def test_revoke_others_retains_current_session(self):
        current, _, _ = self.login()
        other, _, _ = self.login()
        self.assertEqual(
            current.post("/api/v1/auth/sessions/revoke-others").status_code, 200
        )
        self.assertEqual(current.get("/api/v1/auth/me").status_code, 200)
        self.assertEqual(other.get("/api/v1/auth/me").status_code, 401)

    def test_foreign_session_has_same_404_as_unknown(self):
        client, token, _ = self.login()
        user = PlatformUser.objects.create_user(
            email="other@example.test",
            password=self.password,
            tenant=self.tenant,
            status="active",
        )
        other, _, _ = self.login(user.email)
        foreign = other.post("/api/v1/auth/sessions/" + token["session_id"] + "/revoke")
        unknown = other.post("/api/v1/auth/sessions/dss_unknown/revoke")
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.data["error"], unknown.data["error"])
        self.assertEqual(client.get("/api/v1/auth/me").status_code, 200)

    def test_rotation_registers_successor_as_outstanding_and_keeps_one_session(self):
        client, old, _ = self.login()
        response = client.post("/api/v1/auth/refresh")
        self.assertEqual(response.status_code, 200, response.data)
        new = RefreshToken(response.cookies["identitycore_refresh_dashboard"].value)
        self.assertEqual(old["session_id"], new["session_id"])
        self.assertTrue(OutstandingToken.objects.filter(jti=new["jti"]).exists())
        self.assertEqual(DashboardSession.objects.count(), 1)
        self.assertEqual(RefreshTokenSession.objects.count(), 2)

    def test_password_change_revokes_every_session(self):
        client, _, _ = self.login()
        other, _, _ = self.login()
        change_password(
            user=self.user,
            current_password=self.password,
            new_password="ChangedPassword123!",
        )
        self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)
        self.assertEqual(other.post("/api/v1/auth/refresh").status_code, 401)

    def test_logout_does_not_claim_success_on_database_failure(self):
        client, _, _ = self.login()
        with patch(
            "apps.accounts.views.revoke_refresh_token",
            side_effect=OperationalError("database unavailable"),
        ):
            client.raise_request_exception = False
            response = client.post("/api/v1/auth/logout")
        self.assertEqual(response.status_code, 500)

    def test_legacy_refresh_migrates_once_after_signature_validation(self):
        token = RefreshToken.for_user(self.user)
        client = APIClient()
        client.cookies["identitycore_refresh"] = str(token)
        response = client.post("/api/v1/auth/refresh")
        self.assertEqual(response.status_code, 200, response.data)
        new = RefreshToken(response.cookies["identitycore_refresh"].value)
        self.assertIn("session_id", new)
        self.assertEqual(DashboardSession.objects.count(), 1)

    def test_invalid_signature_cannot_revoke_a_real_session(self):
        client, token, _ = self.login()
        encoded = str(token)
        body, signature = encoded.rsplit(".", 1)
        client.cookies["identitycore_refresh_dashboard"] = (
            body + "." + ("a" if signature[0] != "a" else "b") + signature[1:]
        )
        self.assertEqual(client.post("/api/v1/auth/logout").status_code, 200)
        self.assertIsNone(
            DashboardSession.objects.get(public_id=token["session_id"]).revoked_at
        )

    def test_history_cleanup_keeps_live_token_and_recent_session_records(self):
        _, token, _ = self.login()
        row = RefreshTokenSession.objects.get(jti=token["jti"])
        RefreshTokenSession.objects.filter(pk=row.pk).update(
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertEqual(purge_expired_session_history(limit=1), 1)
        self.assertEqual(DashboardSession.objects.count(), 1)

    def test_legacy_replay_revokes_its_migrated_successor(self):
        original_token = RefreshToken.for_user(self.user)
        legacy_access = str(original_token.access_token)
        original = str(original_token)
        client = APIClient()
        client.cookies["identitycore_refresh"] = original
        response = client.post(
            "/api/v1/auth/refresh", HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.cookies["identitycore_refresh"].value, "")
        access = response.data["data"]["tokens"]["access"]
        client.cookies["identitycore_refresh_dashboard"] = original
        self.assertEqual(
            client.post(
                "/api/v1/auth/refresh", HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard"
            ).status_code,
            401,
        )
        client.credentials(HTTP_AUTHORIZATION="Bearer " + access)
        self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + legacy_access)
        self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)

    def test_scoped_cookie_cannot_fall_back_to_legacy_when_invalid(self):
        client = APIClient()
        client.cookies["identitycore_refresh_dashboard"] = "invalid"
        client.cookies["identitycore_refresh"] = str(RefreshToken.for_user(self.user))
        self.assertEqual(
            client.post(
                "/api/v1/auth/refresh", HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard"
            ).status_code,
            401,
        )
        self.assertEqual(DashboardSession.objects.count(), 0)

    def test_signed_token_for_deleted_account_is_an_authentication_error(self):
        client, _, _ = self.login()
        self.user.delete()
        self.assertEqual(client.post("/api/v1/auth/refresh").status_code, 401)
        self.assertEqual(client.post("/api/v1/auth/logout").status_code, 200)

    def test_session_cannot_move_between_application_scopes(self):
        client, _, _ = self.login()
        client.cookies["identitycore_refresh_platform_admin"] = client.cookies[
            "identitycore_refresh_dashboard"
        ].value
        client.credentials(HTTP_X_IDENTITYCORE_SESSION_SCOPE="platform_admin")
        self.assertEqual(client.post("/api/v1/auth/refresh").status_code, 401)
