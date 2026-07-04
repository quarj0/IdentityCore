from django.db import IntegrityError
from django.test import TestCase

from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class TenantModelTests(TestCase):
    def test_tenant_uses_one_to_one_relationship_with_organization(self):
        organization = Organization.objects.create(
            name="Acme University",
            slug="acme-university",
        )
        Tenant.objects.create(
            organization=organization,
            name="Acme Tenant",
            slug="acme-tenant",
        )

        with self.assertRaises(IntegrityError):
            Tenant.objects.create(
                organization=organization,
                name="Duplicate Tenant",
                slug="duplicate-tenant",
            )

    def test_generates_prefixed_public_id(self):
        organization = Organization.objects.create(
            name="Beta Health",
            slug="beta-health",
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Beta Tenant",
            slug="beta-tenant",
        )

        self.assertTrue(tenant.public_id.startswith("ten_"))

# Create your tests here.
