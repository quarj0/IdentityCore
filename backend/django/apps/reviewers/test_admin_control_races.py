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

    def test_expiring_invite_replacement_cannot_outlive_concurrent_acceptance(self):
        from datetime import timedelta
        from threading import Event, local
        from unittest.mock import patch
        from django.utils import timezone
        from apps.access_control.models import Role, RoleScope
        from apps.reviewers.models import PlatformAdminInvitation

        admin = PlatformUser.objects.create_superuser(
            email="replacement-race-admin@example.test",
            password="StrongPassword123!",
            status="active",
        )
        role = Role.objects.create(
            name="Replacement race admin", scope=RoleScope.PLATFORM
        )
        actual_now = timezone.now
        clock = local()

        def controlled_now():
            return getattr(clock, "now", actual_now())

        for attempt in range(3):
            now = actual_now()
            token = PlatformAdminInvitation.generate_token()
            invitation = PlatformAdminInvitation.objects.create(
                email=f"replacement-race-{attempt}@example.test",
                role=role,
                invited_by=admin,
                expires_at=now + timedelta(hours=1),
                token_hash=PlatformAdminInvitation.digest_token(token),
            )
            invitation_locked = Event()
            global_lock_attempted = Event()
            reconciliation_attempted = Event()

            def accept():
                close_old_connections()
                clock.now = now
                global_lock_held = False

                def observe(execute, sql, params, many, context):
                    nonlocal global_lock_held
                    result = execute(sql, params, many, context)
                    if "pg_advisory_xact_lock" in sql:
                        global_lock_held = True
                    if (
                        "reviewers_platformadmininvitation" in sql
                        and "FOR UPDATE" in sql
                    ):
                        invitation_locked.set()
                        waiting = (
                            global_lock_attempted
                            if global_lock_held
                            else reconciliation_attempted
                        )
                        if not waiting.wait(10):
                            raise TimeoutError(
                                "Replacement did not reach its serialization boundary"
                            )
                    return result

                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '10s'")
                        cursor.execute("SET statement_timeout = '15s'")
                    request = RequestFactory().post("/api/graphql")
                    request.user = admin
                    with connection.execute_wrapper(observe):
                        return schema.execute_sync(
                            'mutation($token:String!){acceptPlatformAdminInvitation(token:$token,password:"StrongPassword123!"){mfaRequired user{publicId}}}',
                            variable_values={"token": token},
                            context_value={"request": request},
                        )
                finally:
                    connection.close()

            def replace():
                close_old_connections()
                clock.now = now + timedelta(hours=2)

                def observe(execute, sql, params, many, context):
                    if "pg_advisory_xact_lock" in sql:
                        global_lock_attempted.set()
                    if (
                        sql.startswith("UPDATE")
                        and "reviewers_platformadmininvitation" in sql
                    ):
                        reconciliation_attempted.set()
                    return execute(sql, params, many, context)

                try:
                    if not invitation_locked.wait(10):
                        raise TimeoutError(
                            "Acceptance did not lock the original invitation"
                        )
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '10s'")
                        cursor.execute("SET statement_timeout = '15s'")
                    request = RequestFactory().post("/api/graphql")
                    request.user = PlatformUser.objects.get(pk=admin.pk)
                    with connection.execute_wrapper(observe):
                        return schema.execute_sync(
                            "mutation($email:String!){invitePlatformAdmin(email:$email){invitation{id}}}",
                            variable_values={"email": invitation.email},
                            context_value={"request": request},
                        )
                finally:
                    connection.close()

            with patch(
                "config.graphql_mutations.timezone.now", side_effect=controlled_now
            ), patch("config.graphql_mutations.is_mfa_required", return_value=True):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    accepted_future, replaced_future = pool.submit(accept), pool.submit(
                        replace
                    )
                    accepted, replaced = accepted_future.result(
                        timeout=30
                    ), replaced_future.result(timeout=30)
            self.assertIsNone(accepted.errors, accepted.errors)
            self.assertIsNotNone(replaced.errors)
            self.assertIn("account already exists", replaced.errors[0].message.lower())
            invitation.refresh_from_db()
            self.assertEqual(invitation.status, "accepted")
            self.assertFalse(
                PlatformAdminInvitation.objects.filter(
                    email=invitation.email, status="pending"
                ).exists()
            )
            self.assertEqual(
                PlatformUser.objects.filter(email=invitation.email).count(), 1
            )
            self.assertFalse(
                AuditEvent.objects.filter(action="platform_admin.invited").exists()
            )
