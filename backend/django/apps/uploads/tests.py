from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verifications.models import Verification, VerificationSession, VerificationStatus
from apps.verification_subjects.models import VerificationSubject


class UploadCreateTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Example Bank", slug="example-bank")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Example Tenant",
            slug="example-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="ops@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Akosua Owusu",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding verification",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() + timedelta(hours=24),
            created_by=self.user,
        )
        self.session = VerificationSession(
            verification=self.verification,
            tenant=self.tenant,
            expires_at=self.verification.expires_at,
        )
        self.raw_session_token = "portal-secret-token"
        self.session.set_session_token(self.raw_session_token)
        self.session.save()

    def auth_headers(self, token=None, session_id=None):
        return {
            "HTTP_AUTHORIZATION": f"Bearer {token or self.raw_session_token}",
            "HTTP_X_SESSION_ID": session_id or self.session.public_id,
        }

    def test_create_upload_returns_expiring_upload_url(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["upload_id"].startswith("upl_"))
        self.assertIn(response.data["data"]["upload_id"], response.data["data"]["upload_url"])

    def test_create_upload_requires_session_authentication(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_upload_rejects_unsupported_mime_type(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "application/pdf",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_upload_rejects_video_for_selfie_capture(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "selfie_capture",
                "mime_type": "video/mp4",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mime_type", response.data["error"]["details"])

    def test_create_upload_rejects_image_for_liveness_capture(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "liveness_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mime_type", response.data["error"]["details"])

    def test_create_upload_accepts_video_for_liveness_capture(self):
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "liveness_capture",
                "mime_type": "video/mp4",
                "file_size_bytes": 1024,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["upload_id"].startswith("upl_"))
