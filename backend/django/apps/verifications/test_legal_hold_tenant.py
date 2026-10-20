from datetime import timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, RetentionLegalHold


class LegalHoldTenantTests(TestCase):
    def test_cross_tenant_verification_hold_cannot_be_created_or_reassigned(self):
        org = Organization.objects.create(name="Synthetic", slug="hold")
        tenant = Tenant.objects.create(organization=org, name="Synthetic", slug="hold")
        other_org = Organization.objects.create(name="Other", slug="other-hold")
        other = Tenant.objects.create(
            organization=other_org, name="Other", slug="other-hold"
        )
        subject = VerificationSubject.objects.create(tenant=tenant)
        case = Verification.objects.create(
            tenant=tenant,
            organization=org,
            verification_subject=subject,
            purpose="Synthetic",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        with self.assertRaises(ValidationError):
            RetentionLegalHold.objects.create(
                tenant=other, verification=case, reason="Wrong tenant"
            )
        hold = RetentionLegalHold.objects.create(
            tenant=tenant, verification=case, reason="Valid"
        )
        hold.tenant = other
        with self.assertRaises(ValidationError):
            hold.save()
        hold.refresh_from_db()
        self.assertEqual(hold.tenant_id, tenant.pk)
        RetentionLegalHold.objects.create(tenant=other, reason="Tenant-wide valid")
        # A retained invalid legacy association must still prevent media deletion.
        RetentionLegalHold.objects.filter(pk=hold.pk).update(tenant=other)
        from apps.verifications.retention import has_active_retention_hold

        self.assertTrue(
            has_active_retention_hold(
                tenant_id=tenant.pk, verification_id=case.pk, now=timezone.now()
            )
        )
