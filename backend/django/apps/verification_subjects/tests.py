from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
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


class VerificationSubjectAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme-api")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme API Tenant",
            slug="acme-api-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="subjects@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_lists_tenant_subjects(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            external_reference="customer_123",
            full_name="Kwame Mensah",
            email="kwame@example.com",
        )

        response = self.client.get("/api/v1/subjects/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["results"][0]["id"], subject.public_id)
        self.assertEqual(response.data["data"]["pagination"]["total"], 1)
