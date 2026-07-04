from django.test import TestCase

from apps.organizations.models import Organization, OrganizationStatus


class OrganizationModelTests(TestCase):
    def test_generates_prefixed_public_id(self):
        organization = Organization.objects.create(
            name="Acme University",
            slug="acme-university",
        )

        self.assertTrue(organization.public_id.startswith("org_"))
        self.assertEqual(organization.status, OrganizationStatus.PENDING_REVIEW)

# Create your tests here.
