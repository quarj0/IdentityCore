import json
from unittest.mock import patch

from django.core import signing
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts import tests as fixtures
from apps.accounts.mfa import (
    consume_mfa_token,
    verify_login_challenge,
    verify_challenge,
    MFA_TOKEN_SALT,
    enable_mfa,
    generate_secret,
    issue_mfa_token,
    resolve_mfa_token,
    totp,
)
from apps.accounts.models import MFARecoveryCode
from apps.accounts.sessions import revoke_user_sessions
from common.throttling import MFATransactionRateThrottle


class MFATransactionTests(TestCase):
    setUp = fixtures.MFAEndpointTests.setUp

    def test_legacy_enabled_flag_without_factor_requires_enrollment(self):
        self.user.mfa_enabled = True
        self.user.save(update_fields=["mfa_enabled"])
        client = APIClient()
        response = client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data["data"]["mfa_enrollment_required"])
        proof = response.data["data"]["mfa_token"]
        self.assertEqual(
            client.post(
                reverse("auth-mfa-enroll"), {"mfa_token": proof}, format="json"
            ).status_code,
            200,
        )
        self.user.refresh_from_db()
        from apps.accounts.mfa import is_mfa_required

        self.assertTrue(is_mfa_required(self.user))
        self.assertFalse(self.user.mfa_enabled)

    def test_graphql_password_login_handles_mfa_and_non_mfa(self):
        client = APIClient()
        query = "mutation($email: String!, $password: String!) { login(email: $email, password: $password) { tokens { access } mfaRequired mfaEnrollmentRequired mfaToken } }"
        body = {
            "query": query,
            "variables": {"email": self.user.email, "password": "StrongPassword123!"},
        }
        response = client.post("/api/graphql", body, format="json", HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard")
        self.assertNotIn("errors", response.json())
        payload = response.json()["data"]["login"]
        self.assertTrue(payload["mfaRequired"])
        self.assertIsNone(payload["tokens"])
        self.assertFalse(response.cookies)
        self.assertIsNotNone(payload["mfaToken"])
        from apps.access_control.models import UserRole

        UserRole.objects.filter(user=self.user).delete()
        response = client.post("/api/graphql", body, format="json", HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard")
        self.assertNotIn("errors", response.json())
        payload = response.json()["data"]["login"]
        self.assertFalse(payload["mfaRequired"])
        self.assertTrue(payload["tokens"]["access"])
        from django.conf import settings
        cookie_name = settings.AUTH_REFRESH_COOKIE_NAME + "_dashboard"
        self.assertIn(cookie_name, response.cookies)
        self.assertTrue(response.cookies[cookie_name]["httponly"])
        refreshed = client.post(reverse("auth-refresh"), {}, format="json", HTTP_X_IDENTITYCORE_SESSION_SCOPE="dashboard")
        self.assertEqual(refreshed.status_code, 200, refreshed.data)
        self.assertTrue(refreshed.data["data"]["tokens"]["access"])

    def test_platform_invitation_acceptance_requires_mfa_and_consumes_invitation(self):
        from apps.access_control.models import Role, RoleScope
        from apps.accounts.models import PlatformUser
        from apps.reviewers.models import PlatformAdminInvitation
        from datetime import timedelta

        inviter = PlatformUser.objects.create_user(
            email="inviter@example.test",
            password="StrongPassword123!",
            is_platform_admin=True,
            status="active",
        )
        role = Role.objects.create(
            name="Synthetic staff", scope=RoleScope.PLATFORM, status="active"
        )
        proof = PlatformAdminInvitation.generate_token()
        invitation = PlatformAdminInvitation.objects.create(
            email="new-staff@example.test",
            role=role,
            invited_by=inviter,
            token_hash=PlatformAdminInvitation.digest_token(proof),
            expires_at=timezone.now() + timedelta(hours=1),
        )
        body = {
            "query": "mutation($token: String!, $password: String!) { acceptPlatformAdminInvitation(token: $token, password: $password) { tokens { access } mfaRequired mfaEnrollmentRequired mfaToken } }",
            "variables": {"token": proof, "password": "StrongPassword123!"},
        }
        client = APIClient()
        with override_settings(ADMIN_MFA_REQUIRED_DEFAULT=True):
            response = client.post("/api/graphql", body, format="json")
        self.assertNotIn("errors", response.json())
        payload = response.json()["data"]["acceptPlatformAdminInvitation"]
        self.assertTrue(payload["mfaRequired"])
        self.assertTrue(payload["mfaEnrollmentRequired"])
        self.assertIsNone(payload["tokens"])
        new_user = resolve_mfa_token(payload["mfaToken"], purpose="enrollment")
        self.assertTrue(new_user.is_platform_admin)
        self.assertFalse(new_user.refresh_token_sessions.exists())
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, "accepted")
        self.assertIn("errors", client.post("/api/graphql", body, format="json").json())

    def test_non_ascii_authenticator_digits_are_rejected(self):
        from apps.accounts.mfa import verified_totp_step
        self.assertIsNone(verified_totp_step(generate_secret(), "١٢٣٤٥٦"))

    def test_payload_has_keyed_binding_without_password_hash(self):
        token = issue_mfa_token(self.user, purpose="enrollment")
        payload = signing.loads(token, salt=MFA_TOKEN_SALT)
        self.assertNotIn("password", payload)
        self.assertNotIn(self.user.password, json.dumps(payload))
        self.assertEqual(
            resolve_mfa_token(token, purpose="enrollment").pk, self.user.pk
        )

    def test_password_change_and_session_revocation_invalidate_pending_proof(self):
        token = issue_mfa_token(self.user, purpose="enrollment")
        self.user.set_password("AnotherStrongPassword123!")
        self.user.save(update_fields=["password"])
        with self.assertRaises(ValueError):
            resolve_mfa_token(token, purpose="enrollment")
        token = issue_mfa_token(self.user, purpose="enrollment")
        revoke_user_sessions(self.user)
        with self.assertRaises(ValueError):
            resolve_mfa_token(token, purpose="enrollment")

    def test_deleted_account_cannot_redeem_pending_proof(self):
        token = issue_mfa_token(self.user, purpose="enrollment")
        self.user.deleted_at = timezone.now()
        self.user.save(update_fields=["deleted_at"])
        with self.assertRaises(ValueError):
            resolve_mfa_token(token, purpose="enrollment")

    def test_old_payload_format_is_rejected(self):
        token = signing.dumps(
            {
                "uid": self.user.pk,
                "purpose": "enrollment",
                "password": self.user.password,
            },
            salt="identitycore.mfa.login.v1",
        )
        with self.assertRaises(ValueError):
            resolve_mfa_token(token, purpose="enrollment")

    def test_recovery_codes_have_128_bit_entropy_and_are_not_stored_raw(self):
        codes = enable_mfa(self.user, generate_secret())
        self.assertEqual(len(set(codes)), 10)
        self.assertTrue(all(len(code) == 32 for code in codes))
        stored = set(MFARecoveryCode.objects.values_list("code_hash", flat=True))
        self.assertFalse(stored.intersection(codes))

    def test_enrollment_proof_cannot_reset_an_enabled_factor(self):
        client = APIClient()
        token = issue_mfa_token(self.user, purpose="enrollment")
        enrollment = client.post(
            reverse("auth-mfa-enroll"), {"mfa_token": token}, format="json"
        )
        secret = enrollment.data["data"]["secret"]
        confirmed = client.post(
            reverse("auth-mfa-enroll-confirm"),
            {"mfa_token": token, "code": totp(secret)},
            format="json",
        )
        self.assertEqual(confirmed.status_code, 200)
        code_ids = list(MFARecoveryCode.objects.values_list("pk", flat=True))
        self.assertEqual(
            client.post(
                reverse("auth-mfa-enroll"), {"mfa_token": token}, format="json"
            ).status_code,
            401,
        )
        self.assertEqual(
            client.post(
                reverse("auth-mfa-enroll-confirm"),
                {"mfa_token": token, "code": totp(secret)},
                format="json",
            ).status_code,
            401,
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.mfa_config_json["totp_secret"], secret)
        self.assertEqual(
            list(MFARecoveryCode.objects.values_list("pk", flat=True)), code_ids
        )

    def test_malformed_transaction_request_returns_validation_error(self):
        response = APIClient().post(
            reverse("auth-mfa-enroll"), ["invalid"], format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_peer_bucket_cannot_block_verified_proof_or_rotate_forwarding_keys(
        self,
    ):
        cache.clear()
        self.addCleanup(cache.clear)
        client = APIClient()
        with patch.object(MFATransactionRateThrottle, "rate", "1/min", create=True):
            self.assertEqual(
                client.post(
                    reverse("auth-mfa-enroll"),
                    {"mfa_token": "invalid"},
                    format="json",
                    HTTP_X_FORWARDED_FOR="203.0.113.1",
                ).status_code,
                401,
            )
            self.assertEqual(
                client.post(
                    reverse("auth-mfa-enroll"),
                    {"mfa_token": "invalid"},
                    format="json",
                    HTTP_X_FORWARDED_FOR="203.0.113.2",
                ).status_code,
                429,
            )
            token = issue_mfa_token(self.user, purpose="enrollment")
            self.assertEqual(
                client.post(
                    reverse("auth-mfa-enroll"), {"mfa_token": token}, format="json"
                ).status_code,
                200,
            )
            token = issue_mfa_token(self.user, purpose="enrollment")
            self.assertEqual(
                client.post(
                    reverse("auth-mfa-enroll"), {"mfa_token": token}, format="json"
                ).status_code,
                429,
            )

    def test_totp_step_is_single_use_even_with_a_new_login_proof(self):
        secret = generate_secret()
        enable_mfa(self.user, secret)
        with patch("apps.accounts.mfa.time.time", return_value=1700000000):
            code = totp(secret)
            first = issue_mfa_token(self.user, purpose="challenge")
            self.assertEqual(verify_login_challenge(self.user, first, code), "totp")
            second = issue_mfa_token(self.user, purpose="challenge")
            self.assertIsNone(verify_login_challenge(self.user, second, code))
        with patch("apps.accounts.mfa.time.time", return_value=1700000030):
            code = totp(secret)
            third = issue_mfa_token(self.user, purpose="challenge")
            self.assertEqual(verify_login_challenge(self.user, third, code), "totp")

    def test_replayed_proof_cannot_burn_another_recovery_code(self):
        codes = enable_mfa(self.user, generate_secret())
        proof = issue_mfa_token(self.user, purpose="challenge")
        self.assertEqual(
            verify_login_challenge(self.user, proof, codes[0]), "recovery_code"
        )
        self.assertIsNone(verify_login_challenge(self.user, proof, codes[1]))
        self.assertEqual(
            MFARecoveryCode.objects.filter(used_at__isnull=False).count(), 1
        )
        fresh = issue_mfa_token(self.user, purpose="challenge")
        self.assertEqual(
            verify_login_challenge(self.user, fresh, codes[1]), "recovery_code"
        )

    def test_live_consumed_proofs_are_not_evicted_after_twenty_logins(self):
        proofs = [issue_mfa_token(self.user, purpose="enrollment") for _ in range(25)]
        for proof in proofs:
            self.assertTrue(consume_mfa_token(self.user, proof))
        self.assertFalse(consume_mfa_token(self.user, proofs[0]))

    def test_legacy_recovery_codes_are_upgraded_without_plaintext_and_migration_is_idempotent(
        self,
    ):
        import hashlib
        import hmac
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection

        enable_mfa(self.user, generate_secret())
        raw = "A1B2C3D4E5"
        old = hmac.new(
            str(self.user.pk).encode(), raw.encode(), hashlib.sha256
        ).hexdigest()
        row = MFARecoveryCode.objects.create(user=self.user, code_hash=old)
        migrate = import_module(
            "apps.accounts.migrations.0009_protect_mfa_recovery_digests"
        ).protect_legacy_digests
        migrate(apps, SimpleNamespace(connection=connection))
        row.refresh_from_db()
        protected = row.code_hash
        self.assertTrue(protected.startswith("v2$"))
        self.assertEqual(len(protected), 64)
        self.assertNotEqual(protected, old)
        migrate(apps, SimpleNamespace(connection=connection))
        row.refresh_from_db()
        self.assertEqual(row.code_hash, protected)
        self.assertEqual(verify_challenge(self.user, raw), "recovery_code")
        self.assertIsNone(verify_challenge(self.user, raw))

    def test_pepper_rotation_requires_an_explicit_retained_key(self):
        old = "old-pepper-" + "a" * 64
        new = "new-pepper-" + "b" * 64
        with override_settings(MFA_RECOVERY_PEPPER=old):
            codes = enable_mfa(self.user, generate_secret())
        with override_settings(
            MFA_RECOVERY_PEPPER=new, MFA_RECOVERY_PEPPER_FALLBACKS=[]
        ):
            self.assertIsNone(verify_challenge(self.user, codes[0]))
        with override_settings(
            MFA_RECOVERY_PEPPER=new, MFA_RECOVERY_PEPPER_FALLBACKS=[old]
        ):
            self.assertEqual(verify_challenge(self.user, codes[0]), "recovery_code")

    def test_optional_pepper_configuration_rejects_weak_secrets_without_exposing_values(
        self,
    ):
        from common.configuration import validate_production_environment
        from common.test_configuration import production_environment
        from django.core.exceptions import ImproperlyConfigured

        bad = "private-short-key"
        with self.assertRaises(ImproperlyConfigured) as error:
            validate_production_environment(
                production_environment(MFA_RECOVERY_PEPPER=bad)
            )
        self.assertNotIn(bad, str(error.exception))
        with self.assertRaises(ImproperlyConfigured):
            validate_production_environment(
                production_environment(MFA_RECOVERY_PEPPER_FALLBACKS=json.dumps([bad]))
            )
