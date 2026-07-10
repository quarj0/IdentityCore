from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.uploads.tasks import cleanup_expired_uploads_task
from apps.verifications.models import (
    Verification,
    VerificationSession,
    VerificationStatus,
)
from apps.verification_subjects.models import VerificationSubject


class UploadCreateTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Example Bank", slug="example-bank"
        )
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
        self.assertIn(
            response.data["data"]["upload_id"], response.data["data"]["upload_url"]
        )
        self.assertEqual(
            response.data["data"]["upload_headers"],
            {
                "Content-Type": "image/jpeg",
                "x-amz-server-side-encryption": "AES256",
            },
        )
        self.assertEqual(
            response.data["data"]["upload_transfer_path"],
            f"/uploads/{response.data['data']['upload_id']}/transfer",
        )
        upload = Upload.objects.get(public_id=response.data["data"]["upload_id"])
        self.assertEqual(upload.tenant, self.tenant)
        self.assertEqual(upload.verification, self.verification)
        self.assertEqual(upload.verification_session, self.session)
        self.assertEqual(upload.purpose, UploadPurpose.DOCUMENT_CAPTURE)
        self.assertEqual(upload.status, UploadStatus.INITIATED)
        self.assertEqual(
            upload.storage_key,
            (
                f"organizations/{self.organization.public_id}"
                f"/verifications/{self.verification.public_id}"
                f"/documents/{upload.public_id}"
            ),
        )

    @patch("apps.uploads.views.put_object_bytes")
    def test_transfer_upload_proxies_file_to_private_storage(self, put_object_bytes):
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": 4,
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["upload_id"], upload_id)
        put_object_bytes.assert_called_once()

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


class UploadRetentionTaskTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Example Bank", slug="example-bank-retention"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Example Tenant Retention",
            slug="example-tenant-retention",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="ops-retention@example.com",
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
        self.session.set_session_token("retention-secret-token")
        self.session.save()

    def test_cleanup_expired_uploads_marks_temporary_upload_expired_and_deleted(self):
        expired_upload = Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            purpose=UploadPurpose.DOCUMENT_CAPTURE,
            storage_key=(
                f"organizations/{self.organization.public_id}"
                f"/verifications/{self.verification.public_id}/documents/upl_expired"
            ),
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            status=UploadStatus.INITIATED,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        active_upload = Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            purpose=UploadPurpose.SELFIE_CAPTURE,
            storage_key=(
                f"organizations/{self.organization.public_id}"
                f"/verifications/{self.verification.public_id}/selfies/upl_active"
            ),
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=2048,
            status=UploadStatus.INITIATED,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        cleaned = cleanup_expired_uploads_task(limit=10)

        expired_upload.refresh_from_db()
        active_upload.refresh_from_db()
        self.assertEqual(cleaned, 1)
        self.assertEqual(expired_upload.status, UploadStatus.EXPIRED)
        self.assertIsNotNone(expired_upload.deleted_at)
        self.assertEqual(active_upload.status, UploadStatus.INITIATED)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="retention.temporary_upload_deleted",
                target_id=expired_upload.public_id,
            ).exists()
        )

    def test_cleanup_expired_uploads_deletes_consumed_temp_upload_after_retention_window(self):
        consumed_upload = Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            purpose=UploadPurpose.SELFIE_CAPTURE,
            storage_key=(
                f"organizations/{self.organization.public_id}"
                f"/verifications/{self.verification.public_id}/selfies/upl_consumed"
            ),
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            status=UploadStatus.CONSUMED,
            expires_at=timezone.now() + timedelta(minutes=10),
            consumed_at=timezone.now() - timedelta(hours=25),
        )

        cleaned = cleanup_expired_uploads_task(limit=10)

        consumed_upload.refresh_from_db()
        self.assertEqual(cleaned, 1)
        self.assertEqual(consumed_upload.status, UploadStatus.EXPIRED)
        self.assertIsNotNone(consumed_upload.deleted_at)
