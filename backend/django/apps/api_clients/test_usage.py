from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient as HTTPClient

from apps.api_clients import tests as client_tests
from apps.api_clients.models import APIClient, APIUsageQuota, APIUsageBucket
from apps.api_clients.usage import reserve_request, usage_for_tenant
from apps.projects.models import Project


class UsageTests(TestCase):
    setUp = client_tests.APIClientModelTests.setUp

    def create_api_client(self, environment="sandbox", limit=100):
        project = Project.objects.create(
            tenant=self.tenant,
            name=environment,
            slug=environment,
            environment=environment,
            created_by=self.user,
        )
        client = APIClient(
            tenant=self.tenant,
            project=project,
            name=environment,
            created_by=self.user,
            rate_limit_per_minute=limit,
            scopes_json=["verifications:read"],
        )
        client.set_client_secret("synthetic-test-secret")
        client.save()
        return client

    def test_environment_and_client_limits_are_atomic_and_independent(self):
        sandbox = self.create_api_client(limit=1)
        production = self.create_api_client("production", limit=1)
        self.assertTrue(reserve_request(sandbox)[0])
        allowed, headers, wait = reserve_request(sandbox)
        self.assertFalse(allowed)
        self.assertEqual(headers["X-RateLimit-Client-Minute-Remaining"], "0")
        self.assertGreater(wait, 0)
        self.assertTrue(reserve_request(production)[0])
        usage = usage_for_tenant(self.tenant)
        self.assertEqual([item["minute"]["accepted"] for item in usage], [1, 1])
        self.assertEqual(usage[0]["month"]["accepted"], 1)
        self.assertEqual(usage[0]["month"]["denied"], 1)

    def test_month_limit_does_not_reset_with_minute(self):
        client = self.create_api_client()
        APIUsageQuota.objects.create(
            tenant=self.tenant,
            environment="sandbox",
            requests_per_minute=100,
            requests_per_month=1,
        )
        now = timezone.now().replace(day=10, hour=12, minute=10, second=0)
        self.assertTrue(reserve_request(client, now=now)[0])
        self.assertFalse(reserve_request(client, now=now + timedelta(minutes=2))[0])
        self.assertTrue(
            reserve_request(
                client, now=now.replace(month=11 if now.month != 11 else 12, day=1)
            )[0]
        )

    def test_organization_limit_is_shared_by_clients(self):
        client = self.create_api_client()
        other = APIClient(
            tenant=self.tenant,
            project=client.project,
            name="other",
            created_by=self.user,
            rate_limit_per_minute=100,
        )
        other.set_client_secret("synthetic-other-secret")
        other.save()
        APIUsageQuota.objects.create(
            tenant=self.tenant,
            environment="sandbox",
            requests_per_minute=1,
            requests_per_month=100,
        )
        self.assertTrue(reserve_request(client)[0])
        self.assertFalse(reserve_request(other)[0])
        self.assertEqual(
            APIUsageBucket.objects.get(client_key="", period="minute").accepted, 1
        )

    def test_headers_and_dashboard_usage_are_tenant_scoped(self):
        client = self.create_api_client(limit=1)
        http = HTTPClient()
        headers = {
            "HTTP_X_CLIENT_ID": client.client_id,
            "HTTP_AUTHORIZATION": "Bearer synthetic-test-secret",
        }
        response = http.get("/api/v1/verifications/", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-RateLimit-Environment"], "sandbox")
        response = http.get("/api/v1/verifications/", **headers)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["X-RateLimit-Remaining"], "0")
        self.assertIn("Retry-After", response)
        # API credentials do not authorize organization dashboard telemetry.
        self.assertIn(
            http.get("/api/v1/api-clients/usage", **headers).status_code, (401, 403)
        )
        http.force_authenticate(self.user)
        response = http.get("/api/v1/api-clients/usage?tenant=foreign")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["results"][0]["minute"]["accepted"], 1)
        self.assertNotIn(client.client_id, str(response.data))
        self.assertNotIn("secret", str(response.data))

    def test_soft_deleted_credentials_are_rejected_before_counting(self):
        client = self.create_api_client()
        client.soft_delete()
        http = HTTPClient()
        response = http.get(
            "/api/v1/verifications/",
            HTTP_X_CLIENT_ID=client.client_id,
            HTTP_AUTHORIZATION="Bearer synthetic-test-secret",
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(APIUsageBucket.objects.exists())

    def test_aggregate_retention_removes_old_windows_only(self):
        from apps.api_clients.tasks import cleanup_api_usage_task

        client = self.create_api_client()
        reserve_request(client, now=timezone.now() - timedelta(days=120))
        reserve_request(client)
        self.assertEqual(cleanup_api_usage_task(), 3)
        self.assertEqual(APIUsageBucket.objects.count(), 3)

    def test_calendar_month_rollover_is_utc_and_crosses_year(self):
        from datetime import datetime, timezone as utc

        client = self.create_api_client()
        APIUsageQuota.objects.create(
            tenant=self.tenant,
            environment="sandbox",
            requests_per_minute=100,
            requests_per_month=1,
        )
        self.assertTrue(
            reserve_request(client, now=datetime(2026, 12, 31, 23, 59, tzinfo=utc.utc))[
                0
            ]
        )
        self.assertTrue(
            reserve_request(client, now=datetime(2027, 1, 1, 0, 0, tzinfo=utc.utc))[0]
        )

    def test_api_clients_do_not_consume_dashboard_or_session_throttles(self):
        from unittest.mock import patch
        from common.throttling import (
            DashboardUserRateThrottle,
            VerificationSessionRateThrottle,
        )

        client = self.create_api_client(limit=3)
        http = HTTPClient()
        rates = {"dashboard_user": "1/min", "verification_session": "1/min"}
        with patch.object(
            DashboardUserRateThrottle, "THROTTLE_RATES", rates
        ), patch.object(VerificationSessionRateThrottle, "THROTTLE_RATES", rates):
            for _ in range(3):
                response = http.get(
                    "/api/v1/verifications/",
                    HTTP_X_CLIENT_ID=client.client_id,
                    HTTP_AUTHORIZATION="Bearer synthetic-test-secret",
                    HTTP_X_SESSION_ID="unrelated-principal",
                )
                self.assertEqual(response.status_code, 200)
            denied = http.get(
                "/api/v1/verifications/",
                HTTP_X_CLIENT_ID=client.client_id,
                HTTP_AUTHORIZATION="Bearer synthetic-test-secret",
            )
            self.assertEqual(denied.status_code, 429)
            self.assertEqual(denied["X-RateLimit-Client-Minute-Remaining"], "0")
            http.force_authenticate(self.user)
            self.assertEqual(http.get("/api/v1/api-clients/usage").status_code, 200)
            self.assertEqual(http.get("/api/v1/api-clients/usage").status_code, 429)
        self.assertEqual(
            APIUsageBucket.objects.get(client_key="", period="minute").accepted, 3
        )


@skipUnless(connection.vendor == "postgresql", "Atomic quota races require PostgreSQL")
class UsageRaceTests(TransactionTestCase):
    setUp = client_tests.APIClientModelTests.setUp
    create_api_client = UsageTests.create_api_client

    def test_concurrent_requests_cannot_overspend_any_window(self):
        client = self.create_api_client(limit=4)
        APIUsageQuota.objects.create(
            tenant=self.tenant,
            environment="sandbox",
            requests_per_minute=4,
            requests_per_month=4,
        )
        start = Barrier(12)

        def request():
            close_old_connections()
            try:
                current = APIClient.objects.select_related("project").get(pk=client.pk)
                start.wait(timeout=10)
                return reserve_request(current)[0]
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=12) as pool:
            values = list(pool.map(lambda _: request(), range(12)))
        self.assertEqual(sum(values), 4)
        for bucket in APIUsageBucket.objects.all():
            self.assertEqual(bucket.accepted, 4)
            self.assertEqual(bucket.denied, 8)
