from datetime import timedelta

from django.db import transaction
from django.test import RequestFactory, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser
from apps.audit.models import AuditEvent
from apps.reviewers.models import PlatformAdminInvitation
from config.graphql_schema import schema


@override_settings(
    PLATFORM_INVITATION_BASE_URL="https://admin.example.test/accept-invitation"
)
class HistoricalPlatformAdminControlTests(APITestCase):
    def setUp(self):
        self.actor = PlatformUser.objects.create_superuser(
            email="control-admin@example.test",
            password="StrongPassword123!",
            status="active",
        )
        self.target = PlatformUser.objects.create_superuser(
            email="target-admin@example.test",
            password="StrongPassword123!",
            status="active",
        )

    def graphql(self, query, variables):
        request = RequestFactory().post("/api/graphql")
        request.user = self.actor
        with transaction.atomic():
            result = schema.execute_sync(
                query, variable_values=variables, context_value={"request": request}
            )
            if result.errors:
                transaction.set_rollback(True)
        return result

    def invite(self):
        return self.graphql(
            "mutation($email:String!){invitePlatformAdmin(email:$email){invitation{id}}}",
            {"email": "replacement@example.test"},
        )

    def test_expired_pending_platform_invitation_can_be_replaced(self):
        first = self.invite()
        self.assertIsNone(first.errors, first.errors)
        old = PlatformAdminInvitation.objects.get(
            public_id=first.data["invitePlatformAdmin"]["invitation"]["id"]
        )
        PlatformAdminInvitation.objects.filter(pk=old.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        result = self.invite()
        self.assertIsNone(result.errors, result.errors)
        old.refresh_from_db()
        self.assertEqual(old.status, "expired")
        self.assertNotEqual(
            old.public_id, result.data["invitePlatformAdmin"]["invitation"]["id"]
        )
        self.assertEqual(
            PlatformAdminInvitation.objects.filter(
                email=old.email, status="pending"
            ).count(),
            1,
        )

    def test_tenantless_admin_deactivation_retains_reason_in_platform_audit(self):
        result = self.graphql(
            'mutation($id:String!){deactivatePlatformAdmin(userId:$id,reason:"Confirmed access removal"){publicId status}}',
            {"id": self.target.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        self.target.refresh_from_db()
        self.assertEqual(self.target.status, "inactive")
        events = AuditEvent.objects.filter(
            action="platform_admin.deactivated", target_id=self.target.public_id
        )
        self.assertEqual(events.count(), 1)
        event = events.get()
        self.assertIsNone(event.tenant_id)
        self.assertEqual(event.actor_id, self.actor.public_id)
        self.assertEqual(event.metadata_json["reason"], "Confirmed access removal")

    def test_stale_actor_cannot_invite_after_platform_access_is_revoked(self):
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant

        organization = Organization.objects.create(
            name="Revoked actor", slug="revoked-actor", status="active"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Revoked actor",
            slug="revoked-actor",
            status="active",
        )
        PlatformUser.objects.filter(pk=self.actor.pk).update(
            tenant=tenant, is_platform_admin=False
        )
        result = self.invite()
        self.assertIsNotNone(result.errors)
        self.assertFalse(PlatformAdminInvitation.objects.exists())
        self.assertFalse(
            AuditEvent.objects.filter(action="platform_admin.invited").exists()
        )

    def test_stale_inactive_actor_cannot_invite(self):
        PlatformUser.objects.filter(pk=self.actor.pk).update(status="inactive")
        result = self.invite()
        self.assertIsNotNone(result.errors)
        self.assertFalse(PlatformAdminInvitation.objects.exists())
        self.assertFalse(
            AuditEvent.objects.filter(action="platform_admin.invited").exists()
        )

    def test_tenant_bound_platform_actor_can_invite_and_deactivate_with_valid_audit_scope(
        self,
    ):
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant
        from apps.audit.services import verify_audit_chain

        organization = Organization.objects.create(
            name="Bound admin", slug="bound-admin", status="active"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Bound admin",
            slug="bound-admin",
            status="active",
        )
        self.actor.tenant = tenant
        self.actor.save(update_fields=["tenant"])
        operations = [
            ("invited", lambda: self.invite()),
            (
                "deactivated",
                lambda: self.graphql(
                    'mutation($id:String!){deactivatePlatformAdmin(userId:$id,reason:"Bound administrator removal"){publicId status}}',
                    {"id": self.target.public_id},
                ),
            ),
        ]
        for suffix, operation in operations:
            with self.subTest(operation=suffix):
                result = operation()
                self.assertIsNone(result.errors, result.errors)
                event = AuditEvent.objects.get(action="platform_admin." + suffix)
                self.assertEqual(event.tenant_id, tenant.pk)
                self.assertEqual(event.actor_id, self.actor.public_id)
                if suffix == "deactivated":
                    self.assertEqual(
                        event.metadata_json["reason"], "Bound administrator removal"
                    )
        self.assertEqual(verify_audit_chain(tenant_id=tenant.pk), (True, ""))
