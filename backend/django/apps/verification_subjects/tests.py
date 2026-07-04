from django.test import TestCase

from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject


class VerificationSubjectModelTests(TestCase):
    def test_generates_prefixed_public_id(self):
        organization = Organization.objects.create(name="Acme", slug="acme")
        tenant = Tenant.objects.create(
            organization=organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant,
            external_reference="customer_123",
            full_name="Kwame Mensah",
        )

        self.assertTrue(subject.public_id.startswith("sub_"))
