from django.test import TestCase
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from apps.organizations.models import Organization, OrganizationStatus
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.tenants.models import Tenant
from apps.organizations.models import OrganizationSupportingDocument
from apps.organizations.onboarding import resend_onboarding_email_verification, serialize_onboarding_state
from apps.notifications.models import Notification


class OrganizationModelTests(TestCase):
    def test_generates_prefixed_public_id(self):
        organization = Organization.objects.create(
            name="Acme University",
            slug="acme-university",
        )

        self.assertTrue(organization.public_id.startswith("org_"))
        self.assertEqual(len(organization.public_id.split("_", maxsplit=1)[1]), 26)
        self.assertEqual(organization.status, OrganizationStatus.PENDING_REVIEW)

class OrganizationBrandingTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme University",
            slug="acme-university-branding",
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-branding",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="branding@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_branding_asset_upload_uses_public_bucket_keyspace(self):
        response = self.client.post(
            reverse("organization-branding-asset-upload"),
            {
                "asset_type": "logo",
                "filename": "logo.png",
                "mime_type": "image/png",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(f"organizations/{self.organization.public_id}/branding/logos/", response.data["data"]["storage_key"])

    def test_patch_organization_branding_sets_logo_url_from_public_storage_key(self):
        logo_storage_key = (
            f"organizations/{self.organization.public_id}/branding/logos/{self.organization.public_id}.png"
        )

        response = self.client.patch(
            reverse("organization-detail"),
            {"logo_storage_key": logo_storage_key},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.settings_json["logo_storage_key"], logo_storage_key)
        self.assertTrue(response.data["data"]["settings"]["logo_url"])


class OrganizationSupportingDocumentTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme University",
            slug="acme-university-docs",
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-docs",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="docs@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_document_upload_returns_transfer_path(self):
        response = self.client.post(
            reverse("organization-document-upload"),
            {
                "filename": "certificate.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 12345,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["data"]["upload_transfer_path"],
            f"/organization/me/verification-documents/{response.data['data']['document_id']}/transfer/",
        )

    @patch("apps.organizations.views.put_object_bytes")
    def test_document_upload_transfer_stores_file_server_side(self, mock_put_object_bytes):
        document = OrganizationSupportingDocument.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            uploaded_by=self.user,
            filename="certificate.pdf",
            mime_type="application/pdf",
            file_size_bytes=12,
            storage_key="organizations/org_01TEST/verification/certificate.pdf",
            status="initiated",
        )

        response = self.client.post(
            reverse(
                "organization-document-upload-transfer",
                kwargs={"document_id": document.public_id},
            ),
            {"file": SimpleUploadedFile("certificate.pdf", b"hello world!", content_type="application/pdf")},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_put_object_bytes.assert_called_once()

    @override_settings(PUBLIC_ASSET_URL_BASE="https://assets.example.com/public")
    def test_onboarding_state_uses_public_asset_urls_for_supporting_documents(self):
        OrganizationSupportingDocument.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            uploaded_by=self.user,
            filename="certificate.pdf",
            mime_type="application/pdf",
            file_size_bytes=12345,
            storage_key="organizations/org_01TEST/verification/certificate.pdf",
            status="uploaded",
        )

        onboarding = serialize_onboarding_state(
            organization=self.organization,
            tenant=self.tenant,
            user=self.user,
        )

        self.assertEqual(
            onboarding["supporting_documents"][0]["download_url"],
            "https://assets.example.com/public/organizations/org_01TEST/verification/certificate.pdf",
        )


class OrganizationOnboardingEmailTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme University",
            slug="acme-university-onboarding",
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-onboarding",
            status="pending_review",
        )
        self.user = PlatformUser.objects.create_user(
            email="pending@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.INACTIVE,
            tenant=self.tenant,
        )

    def test_resend_onboarding_email_verification_creates_fresh_verification_link(self):
        sent = resend_onboarding_email_verification(
            business_email=self.user.email,
        )

        self.assertTrue(sent)
        self.assertTrue(
            Notification.objects.filter(
                tenant=self.tenant,
                recipient=self.user.email,
                template_code="account.email_verification",
            ).exists()
        )
