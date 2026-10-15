from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import RequestFactory
from rest_framework.test import APITransactionTestCase

from apps.accounts.models import PlatformUser
from apps.audit.models import AuditEvent
from apps.audit.services import verify_audit_chain
from config.graphql_schema import schema


@skipUnless(
    connection.vendor == "postgresql",
    "Requires real PostgreSQL transactional advisory locks",
)
class PlatformAdminControlRaceTests(APITransactionTestCase):
    def test_concurrent_cross_deactivation_preserves_an_active_admin(self):
        users = [
            PlatformUser.objects.create_superuser(
                email=f"admin-race-{index}@example.test",
                password="StrongPassword123!",
                status="active",
            )
            for index in range(2)
        ]
        for attempt in range(3):
            PlatformUser.objects.filter(pk__in=[user.pk for user in users]).update(
                status="active"
            )
            start = Barrier(2)

            def deactivate(index):
                close_old_connections()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '10s'")
                        cursor.execute("SET statement_timeout = '15s'")
                    request = RequestFactory().post("/api/graphql")
                    request.user = PlatformUser.objects.get(pk=users[index].pk)
                    start.wait(timeout=10)
                    result = schema.execute_sync(
                        'mutation($id:String!){deactivatePlatformAdmin(userId:$id,reason:"Synthetic concurrent deactivation"){publicId status}}',
                        variable_values={"id": users[1 - index].public_id},
                        context_value={"request": request},
                    )
                    return bool(result.errors)
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=2) as pool:
                first, second = pool.submit(deactivate, 0), pool.submit(deactivate, 1)
                failures = [first.result(timeout=25), second.result(timeout=25)]
            self.assertEqual(sorted(failures), [False, True])
            self.assertEqual(
                PlatformUser.objects.filter(
                    is_platform_admin=True, status="active"
                ).count(),
                1,
            )
            self.assertEqual(
                AuditEvent.objects.filter(action="platform_admin.deactivated").count(),
                attempt + 1,
            )
            self.assertEqual(verify_audit_chain(tenant_id=None), (True, ""))
