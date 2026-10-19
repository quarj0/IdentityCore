from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase

from apps.audit.models import AuditEvent
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class AuditVerifierCommandTests(TestCase):
    def test_checks_tenant_platform_and_fails_on_corruption(self):
        organization = Organization.objects.create(
            name="Synthetic", slug="verify-audit"
        )
        tenant = Tenant.objects.create(
            organization=organization, name="Synthetic", slug="verify-audit"
        )
        event = AuditEvent.objects.create(
            tenant=tenant,
            actor_type="system",
            action="synthetic",
            target_type="synthetic",
            target_id="synthetic",
        )
        output = StringIO()
        call_command("verify_audit_integrity", tenant=tenant.public_id, stdout=output)
        self.assertIn(f"{tenant.public_id}: valid", output.getvalue())
        call_command("verify_audit_integrity", platform=True, stdout=output)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_auditevent SET action = %s WHERE id = %s",
                ["altered", event.pk],
            )
        errors = StringIO()
        with self.assertRaisesMessage(CommandError, "failed for 1 scope"):
            call_command(
                "verify_audit_integrity", all=True, stdout=output, stderr=errors
            )
        self.assertIn(event.public_id, errors.getvalue())
        self.assertNotIn("altered", errors.getvalue())
        with self.assertRaisesMessage(CommandError, "Unknown tenant"):
            call_command("verify_audit_integrity", tenant="ten_missing")
