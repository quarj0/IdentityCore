from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import override_settings
from rest_framework.test import APIClient, APITransactionTestCase

from apps.verification_sessions import test_handoff
from apps.verifications.models import VerificationMobileHandoff, VerificationSession


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
@override_settings(VERIFICATION_PORTAL_BASE_URL="https://verify.example.test/verify")
class MobileHandoffRaceTests(APITransactionTestCase):
    setUp = test_handoff.HandoffLifecycleTests.setUp
    session_headers = test_handoff.HandoffLifecycleTests.session_headers
    create = test_handoff.HandoffLifecycleTests.create

    def parallel(self, function):
        barrier = Barrier(2)

        def run(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return function(index)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, range(2)))

    def test_simultaneous_claim_has_one_mobile_session(self):
        claim = self.create()
        results = self.parallel(
            lambda _: APIClient()
            .post(
                "/api/v1/sessions/mobile-handoff/redeem",
                {"handoff": claim, "session_id": self.session.public_id},
                format="json",
            )
            .status_code
        )
        self.assertEqual(sorted(results), [200, 400])
        self.assertEqual(VerificationSession.objects.count(), 2)

    def test_simultaneous_creation_leaves_one_live_claim(self):
        results = self.parallel(
            lambda _: APIClient()
            .post(
                f"/api/v1/sessions/{self.session.public_id}/mobile-handoff",
                {},
                format="json",
                **self.session_headers(),
            )
            .status_code
        )
        self.assertEqual(results, [200, 200])
        from django.utils import timezone

        self.assertEqual(
            VerificationMobileHandoff.objects.filter(
                redeemed_at__isnull=True, expires_at__gt=timezone.now()
            ).count(),
            1,
        )
