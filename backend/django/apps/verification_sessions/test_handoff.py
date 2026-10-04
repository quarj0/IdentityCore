from urllib.parse import urlsplit
from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from apps.verification_sessions import tests as session_tests
from apps.verifications.models import VerificationMobileHandoff, VerificationSession


@override_settings(VERIFICATION_PORTAL_BASE_URL="https://verify.example.test/verify")
class HandoffLifecycleTests(APITestCase):
    setUp = session_tests.VerificationSessionPortalTests.setUp
    session_headers = session_tests.VerificationSessionPortalTests.session_headers

    def create(self):
        response = self.client.post(
            f"/api/v1/sessions/{self.session.public_id}/mobile-handoff",
            {},
            format="json",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        url = urlsplit(response.data["data"]["handoff_url"])
        self.assertEqual(url.query, "")
        self.assertTrue(url.fragment.startswith("handoff="))
        self.assertLessEqual(
            VerificationMobileHandoff.objects.latest("created_at").expires_at,
            timezone.now() + timedelta(minutes=5),
        )
        return url.fragment.removeprefix("handoff=")

    def redeem(self, claim, source=None):
        return APIClient().post(
            "/api/v1/sessions/mobile-handoff/redeem",
            {"handoff": claim, "session_id": source or self.session.public_id},
            format="json",
        )

    def test_single_use_claim_and_fresh_cookie_credential(self):
        claim = self.create()
        first = self.redeem(claim)
        self.assertEqual(first.status_code, 200, first.data)
        self.assertNotEqual(first.data["data"]["session_token"], self.raw_session_token)
        self.assertEqual(self.redeem(claim).status_code, 400)
        self.assertEqual(VerificationSession.objects.count(), 2)
        self.assertNotIn(claim, str(self.tenant.audit_events.values("metadata_json")))

    def test_cross_session_claim_fails_without_consuming_capability(self):
        claim = self.create()
        self.assertEqual(self.redeem(claim, "ses_other_case").status_code, 400)
        self.assertEqual(self.redeem(claim).status_code, 200)

    def test_new_qr_invalidates_previous_unredeemed_claim(self):
        old = self.create()
        new = self.create()
        self.assertEqual(self.redeem(old).status_code, 400)
        self.assertEqual(self.redeem(new).status_code, 200)

    def test_expired_and_revoked_source_cannot_be_redeemed(self):
        claim = self.create()
        VerificationSession.objects.filter(pk=self.session.pk).update(status="revoked")
        self.assertEqual(self.redeem(claim).status_code, 400)
        VerificationSession.objects.filter(pk=self.session.pk).update(
            status="active", expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertEqual(self.redeem(claim).status_code, 400)
        self.assertEqual(VerificationSession.objects.count(), 1)

    def test_suspended_tenant_and_terminal_case_cannot_issue_mobile_credentials(self):
        claim = self.create()
        self.tenant.status = "suspended"
        self.tenant.save(update_fields=["status"])
        self.assertEqual(self.redeem(claim).status_code, 400)
        self.tenant.status = "active"
        self.tenant.save(update_fields=["status"])
        self.verification.status = "cancelled"
        self.verification.save(update_fields=["status"])
        self.assertEqual(self.redeem(claim).status_code, 400)

    def test_missing_source_and_oversized_claim_fail_before_password_checks(self):
        claim = self.create()
        response = APIClient().post(
            "/api/v1/sessions/mobile-handoff/redeem", {"handoff": claim}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.redeem("x" * 200).status_code, 400)

    def test_handoff_redeem_has_a_public_brute_force_limit(self):
        from django.core.cache import cache
        from unittest.mock import patch

        cache.clear()
        with patch(
            "common.throttling.SensitivePublicRateThrottle.get_rate",
            return_value="1/min",
        ):
            self.assertEqual(self.redeem("invalid").status_code, 400)
            self.assertEqual(self.redeem("invalid").status_code, 429)
        cache.clear()

    def test_existing_source_bearer_cannot_access_a_suspended_tenant(self):
        self.tenant.status = "suspended"
        self.tenant.save(update_fields=["status"])
        response = self.client.get(
            f"/api/v1/sessions/{self.session.public_id}", **self.session_headers()
        )
        self.assertEqual(response.status_code, 401)
