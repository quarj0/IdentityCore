from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import PlatformUser
from apps.accounts.mfa import totp
from apps.audit.models import AuditEvent
from apps.audit.services import record_audit_event, lock_audit_chain, verify_audit_chain
from apps.audit.serializers import serialize_audit_event
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


@override_settings(ADMIN_MFA_REQUIRED_DEFAULT=True)
class PlatformMFAAuditTests(TestCase):
    def test_tenantless_administrator_can_enroll_and_confirm_with_authenticated_audits(
        self,
    ):
        user = PlatformUser.objects.create_user(
            email="platform-fixture@example.com",
            password="FixturePassword123!",
            is_platform_admin=True,
            status="active",
        )
        client = APIClient()
        response = client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "FixturePassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        token = response.data["data"]["mfa_token"]
        response = client.post(
            reverse("auth-mfa-enroll"), {"mfa_token": token}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        secret = response.data["data"]["secret"]
        response = client.post(
            reverse("auth-mfa-enroll-confirm"),
            {"mfa_token": token, "code": totp(secret)},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant__isnull=True,
                actor_id=user.public_id,
                action="user.mfa_enrollment_started",
            ).exists()
        )
        self.assertEqual(verify_audit_chain(tenant_id=None), (True, ""))
        event = AuditEvent.objects.filter(tenant__isnull=True).first()
        self.assertEqual(serialize_audit_event(event)["actor_display_name"], user.email)
        organization = Organization.objects.create(
            name="Tenant fixture", slug="tenant-fixture"
        )
        tenant = Tenant.objects.create(
            organization=organization, name="Tenant fixture", slug="tenant-fixture"
        )
        tenant_user = PlatformUser.objects.create_user(
            email="tenant-fixture@example.com",
            password="FixturePassword123!",
            tenant=tenant,
            status="active",
        )
        client.force_authenticate(tenant_user)
        response = client.get(reverse("audit-event-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["results"], [])
        response = client.get(
            reverse("audit-event-list").rstrip("/") + "/" + event.public_id
        )
        self.assertEqual(response.status_code, 404)
        with self.assertRaises(ValidationError):
            record_audit_event(
                actor=tenant_user,
                action="fixture",
                target_type="fixture",
                target_id="fixture",
            )
        with self.assertRaises(ValidationError):
            record_audit_event(
                action="fixture", target_type="fixture", target_id="fixture"
            )

    def test_platform_chain_uses_a_distinct_postgres_transaction_lock(self):
        with patch("django.db.connection.vendor", "postgresql"), patch(
            "django.db.connection.cursor"
        ) as cursor:
            lock_audit_chain(None)
        cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
            "SELECT pg_advisory_xact_lock(%s, %s)", [0x49434155, 0]
        )
