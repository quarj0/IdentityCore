from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from rest_framework.test import APIClient, APITransactionTestCase

from apps.accounts.models import DashboardSession
from apps.accounts.sessions import rotate_refresh_token
from apps.accounts import test_sessions
from rest_framework_simplejwt.exceptions import TokenError


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class DashboardSessionRaceTests(APITransactionTestCase):
    password = test_sessions.DashboardSessionTests.password
    setUp = test_sessions.DashboardSessionTests.setUp
    login = test_sessions.DashboardSessionTests.login

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

    def test_concurrent_refresh_has_one_success_and_revokes_replayed_family(self):
        _, token, _ = self.login()

        def rotate(_):
            try:
                rotate_refresh_token(str(token))
                return 200
            except TokenError:
                return 401

        self.assertEqual(sorted(self.parallel(rotate)), [200, 401])
        self.assertIsNotNone(
            DashboardSession.objects.get(public_id=token["session_id"]).revoked_at
        )

    def test_concurrent_refresh_cannot_restore_a_revoked_session(self):
        _, token, _ = self.login()
        manager, _, access = self.login()

        def act(index):
            if index == 0:
                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION="Bearer " + access)
                return client.post(
                    "/api/v1/auth/sessions/" + token["session_id"] + "/revoke"
                ).status_code
            try:
                rotate_refresh_token(str(token))
                return 200
            except TokenError:
                return 401

        results = self.parallel(act)
        self.assertEqual(results[0], 200)
        self.assertIn(results[1], [200, 401])
        self.assertIsNotNone(
            DashboardSession.objects.get(public_id=token["session_id"]).revoked_at
        )
        self.assertEqual(manager.get("/api/v1/auth/me").status_code, 200)
