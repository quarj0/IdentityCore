from datetime import timedelta
from unittest.mock import ANY, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.uploads.tasks import cleanup_expired_uploads_task
from apps.uploads.scanning import inspect_upload_content
from apps.verification_sessions.serializers import resolve_session_upload
from apps.verifications.models import (
    VERIFICATION_SESSION_ACTIONS,
    Verification,
    VerificationSession,
    VerificationStatus,
)
from apps.verification_subjects.models import VerificationSubject


def _iso_box(box_type: bytes, payload: bytes) -> bytes:
    return (len(payload) + 8).to_bytes(4, "big") + box_type + payload


def _iso_video(*, major_brand: bytes = b"isom", handler_type: bytes = b"vide") -> bytes:
    ftyp = _iso_box(b"ftyp", major_brand + b"\x00\x00\x00\x00" + major_brand)
    sample_entry = bytearray(78)
    sample_entry[6:8] = (1).to_bytes(2, "big")
    sample_entry[24:26] = (640).to_bytes(2, "big")
    sample_entry[26:28] = (480).to_bytes(2, "big")
    sample_entry[40:42] = (1).to_bytes(2, "big")
    sample_entry[74:76] = (24).to_bytes(2, "big")
    sample_description = _iso_box(
        b"stsd",
        b"\x00" * 4
        + (1).to_bytes(4, "big")
        + _iso_box(b"avc1", bytes(sample_entry) + _iso_box(b"avcC", b"\x01")),
    )
    sample_table = _iso_box(
        b"stbl",
        sample_description
        + _iso_box(b"stts", b"\x00" * 4 + (1).to_bytes(4, "big") + b"\x00" * 8)
        + _iso_box(b"stsc", b"\x00" * 4 + (1).to_bytes(4, "big") + b"\x00" * 12)
        + _iso_box(
            b"stsz",
            b"\x00" * 8 + (1).to_bytes(4, "big") + (11).to_bytes(4, "big"),
        )
        + _iso_box(
            b"stco",
            b"\x00" * 4 + (1).to_bytes(4, "big") + (100).to_bytes(4, "big"),
        ),
    )
    handler = _iso_box(b"hdlr", b"\x00" * 8 + handler_type + b"\x00" * 12)
    media_info = _iso_box(
        b"minf",
        _iso_box(b"vmhd", b"\x00" * 12)
        + _iso_box(b"dinf", _iso_box(b"dref", b"\x00" * 8))
        + sample_table,
    )
    media = _iso_box(b"mdia", _iso_box(b"mdhd", b"\x00" * 24) + handler + media_info)
    track = _iso_box(b"trak", _iso_box(b"tkhd", b"\x00" * 84) + media)
    movie = _iso_box(b"moov", _iso_box(b"mvhd", b"\x00" * 100) + track)
    return ftyp + movie + _iso_box(b"mdat", b"video-frame")


def _ebml_element(element_id: bytes, payload: bytes) -> bytes:
    if len(payload) >= 0x7F:
        raise ValueError("Test EBML payload is too large for its one-byte size.")
    return element_id + bytes([0x80 | len(payload)]) + payload


def _webm_video(*, track_type: int = 1, codec_id: bytes = b"V_VP9") -> bytes:
    header = _ebml_element(
        b"\x1a\x45\xdf\xa3",
        _ebml_element(b"\x42\x86", b"\x01")
        + _ebml_element(b"\x42\xf7", b"\x01")
        + _ebml_element(b"\x42\xf2", b"\x04")
        + _ebml_element(b"\x42\xf3", b"\x08")
        + _ebml_element(b"\x42\x82", b"webm")
        + _ebml_element(b"\x42\x85", b"\x02"),
    )
    info = _ebml_element(
        b"\x15\x49\xa9\x66",
        _ebml_element(b"\x2a\xd7\xb1", b"\x0f\x42\x40")
        + _ebml_element(b"\x4d\x80", b"IdentityCore")
        + _ebml_element(b"\x57\x41", b"IdentityCore"),
    )
    video = _ebml_element(
        b"\xe0",
        _ebml_element(b"\xb0", (640).to_bytes(2, "big"))
        + _ebml_element(b"\xba", (480).to_bytes(2, "big")),
    )
    track_entry = _ebml_element(
        b"\xae",
        _ebml_element(b"\xd7", b"\x01")
        + _ebml_element(b"\x73\xc5", b"\x01")
        + _ebml_element(b"\x83", bytes([track_type]))
        + _ebml_element(b"\x86", codec_id)
        + video,
    )
    tracks = _ebml_element(b"\x16\x54\xae\x6b", track_entry)
    cluster = _ebml_element(
        b"\x1f\x43\xb6\x75",
        _ebml_element(b"\xe7", b"\x00")
        + _ebml_element(b"\xa3", b"\x81\x00\x00\x80video-frame"),
    )
    return header + _ebml_element(b"\x18\x53\x80\x67", info + tracks + cluster)


class UploadVideoInspectionTests(TestCase):
    def assert_video_result(
        self, content: bytes, mime_type: str, *, expected_safe: bool
    ) -> None:
        safe, reason = inspect_upload_content(
            content=content,
            declared_mime_type=mime_type,
        )
        self.assertEqual(safe, expected_safe)
        self.assertEqual(reason, "" if expected_safe else "video_container_unrecognized")

    def test_accepts_structurally_valid_supported_video_containers(self):
        fixtures = (
            (_iso_video(), "video/mp4"),
            (_iso_video(major_brand=b"qt  "), "video/quicktime"),
            (_webm_video(), "video/webm"),
        )

        for content, mime_type in fixtures:
            with self.subTest(mime_type=mime_type):
                self.assert_video_result(content, mime_type, expected_safe=True)

    def test_rejects_magic_byte_only_video_impostors(self):
        fixtures = (
            (b"\x00\x00\x00\x0cftypisom", "video/mp4"),
            (b"\x1a\x45\xdf\xa3", "video/webm"),
        )

        for content, mime_type in fixtures:
            with self.subTest(mime_type=mime_type):
                self.assert_video_result(content, mime_type, expected_safe=False)

    def test_rejects_truncated_iso_box(self):
        content = _iso_video()[:-1]

        self.assert_video_result(content, "video/mp4", expected_safe=False)

    def test_rejects_iso_audio_only_track(self):
        self.assert_video_result(
            _iso_video(handler_type=b"soun"),
            "video/mp4",
            expected_safe=False,
        )

    def test_rejects_iso_brand_that_does_not_match_declared_type(self):
        self.assert_video_result(
            _iso_video(major_brand=b"qt  "),
            "video/mp4",
            expected_safe=False,
        )

    def test_rejects_webm_without_video_track(self):
        self.assert_video_result(
            _webm_video(track_type=2, codec_id=b"A_OPUS"),
            "video/webm",
            expected_safe=False,
        )

    def test_rejects_webm_with_unsupported_video_codec(self):
        self.assert_video_result(
            _webm_video(codec_id=b"V_MPEG4"),
            "video/webm",
            expected_safe=False,
        )


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
            allowed_actions_json=list(VERIFICATION_SESSION_ACTIONS),
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
            response.data["data"]["upload_complete_path"],
            f"/uploads/{upload.public_id}/complete",
        )
        self.assertEqual(
            upload.storage_key,
            (
                f"organizations/{self.organization.public_id}"
                f"/verifications/{self.verification.public_id}"
                f"/documents/{upload.public_id}"
            ),
        )

    @patch("apps.uploads.views.inspect_upload_content", return_value=(True, ""))
    @patch("apps.uploads.views.put_object_bytes")
    def test_transfer_upload_proxies_file_to_private_storage(
        self, put_object_bytes, inspect_upload_content
    ):
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
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.UPLOADED)
        self.assertEqual(
            upload.checksum_sha256,
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        )

        duplicate_response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {"file": SimpleUploadedFile("document.jpg", b"test", content_type="image/jpeg")},
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(duplicate_response.status_code, status.HTTP_200_OK)
        put_object_bytes.assert_called_once()

        upload.status = UploadStatus.CONSUMED
        upload.consumed_at = timezone.now()
        upload.save(update_fields=["status", "consumed_at", "updated_at"])
        consumed_retry = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(consumed_retry.status_code, status.HTTP_200_OK)
        put_object_bytes.assert_called_once()

    @patch("apps.uploads.views.inspect_upload_content", return_value=(True, ""))
    @patch("apps.uploads.views.put_object_bytes")
    def test_duplicate_transfer_with_different_content_is_rejected(
        self, put_object_bytes, inspect_upload_content
    ):
        create_response = self.client.post(
            reverse("upload-create"),
            {"purpose": "document_capture", "mime_type": "image/jpeg", "file_size_bytes": 4},
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]
        self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {"file": SimpleUploadedFile("document.jpg", b"test", content_type="image/jpeg")},
            format="multipart",
            **self.auth_headers(),
        )

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {"file": SimpleUploadedFile("document.jpg", b"nope", content_type="image/jpeg")},
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        put_object_bytes.assert_called_once()

    @patch("apps.uploads.views.inspect_upload_content")
    @patch("apps.uploads.views.put_object_bytes")
    def test_unsafe_retry_is_scanned_but_does_not_quarantine_validated_upload(
        self, put_object_bytes, inspect_upload_content
    ):
        inspect_upload_content.side_effect = [
            (True, ""),
            (False, "image_content_unrecognized"),
        ]
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
        self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"test", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "document.jpg", b"nope", content_type="image/jpeg"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "upload_quarantined")
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.UPLOADED)
        self.assertEqual(upload.quarantine_reason, "")
        self.assertEqual(inspect_upload_content.call_count, 2)
        put_object_bytes.assert_called_once()

    @patch("apps.uploads.views.put_object_bytes")
    def test_unrecognized_content_is_quarantined_before_processing(self, put_object_bytes):
        create_response = self.client.post(
            reverse("upload-create"),
            {"purpose": "document_capture", "mime_type": "image/jpeg", "file_size_bytes": 4},
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {"file": SimpleUploadedFile("document.jpg", b"test", content_type="image/jpeg")},
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.QUARANTINED)
        self.assertEqual(upload.quarantine_reason, "image_content_unrecognized")
        put_object_bytes.assert_not_called()

    @patch("apps.uploads.views.put_object_bytes")
    def test_magic_only_liveness_video_is_quarantined_before_processing(
        self, put_object_bytes
    ):
        content = b"\x1a\x45\xdf\xa3"
        create_response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "liveness_capture",
                "mime_type": "video/webm",
                "file_size_bytes": len(content),
            },
            format="json",
            **self.auth_headers(),
        )
        upload_id = create_response.data["data"]["upload_id"]

        response = self.client.post(
            reverse("upload-transfer", kwargs={"upload_id": upload_id}),
            {
                "file": SimpleUploadedFile(
                    "liveness.webm", content, content_type="video/webm"
                )
            },
            format="multipart",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "upload_quarantined")
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.QUARANTINED)
        self.assertEqual(upload.quarantine_reason, "video_container_unrecognized")
        put_object_bytes.assert_not_called()

    @patch("apps.uploads.views.delete_object")
    @patch("apps.uploads.views.put_object_bytes")
    @patch("apps.uploads.views.inspect_upload_content", return_value=(True, ""))
    @patch(
        "apps.uploads.views.get_object_bytes",
        return_value=(b"test", "image/jpeg"),
    )
    def test_complete_validates_direct_upload_into_immutable_key(
        self,
        get_object_bytes,
        inspect_upload_content,
        put_object_bytes,
        delete_object,
    ):
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
        upload = Upload.objects.get(public_id=upload_id)
        original_key = upload.storage_key

        response = self.client.post(
            reverse("upload-complete", kwargs={"upload_id": upload_id}),
            {},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        upload.refresh_from_db()
        self.assertEqual(upload.status, UploadStatus.UPLOADED)
        self.assertNotEqual(upload.storage_key, original_key)
        self.assertTrue(upload.storage_key.startswith(f"{original_key}.validated."))
        get_object_bytes.assert_called_once_with(
            bucket_name=ANY,
            key=original_key,
            max_bytes=4,
        )
        put_object_bytes.assert_called_once_with(
            bucket_name=ANY,
            key=upload.storage_key,
            content=b"test",
            content_type="image/jpeg",
        )
        delete_object.assert_called_once_with(bucket_name=ANY, key=original_key)

        retry = self.client.post(
            reverse("upload-complete", kwargs={"upload_id": upload_id}),
            {},
            format="json",
            **self.auth_headers(),
        )
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        get_object_bytes.assert_called_once()

    @patch("apps.uploads.views.delete_object")
    @patch("apps.uploads.views.put_object_bytes")
    @patch(
        "apps.uploads.views.get_object_bytes",
        return_value=(b"test", "image/jpeg"),
    )
    def test_unsafe_direct_upload_is_quarantined_without_copying_bytes(
        self, get_object_bytes, put_object_bytes, delete_object
    ):
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
            reverse("upload-complete", kwargs={"upload_id": upload_id}),
            {},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "upload_quarantined")
        upload = Upload.objects.get(public_id=upload_id)
        self.assertEqual(upload.status, UploadStatus.QUARANTINED)
        self.assertEqual(upload.quarantine_reason, "image_content_unrecognized")
        get_object_bytes.assert_called_once()
        put_object_bytes.assert_not_called()
        delete_object.assert_not_called()

    def test_initiated_direct_upload_cannot_be_submitted_as_evidence(self):
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

        with self.assertRaisesMessage(
            serializers.ValidationError,
            "Upload must be completed and validated before submission.",
        ):
            resolve_session_upload(
                verification_session=self.session,
                upload_id=create_response.data["data"]["upload_id"],
                purpose=UploadPurpose.DOCUMENT_CAPTURE,
            )

    @patch(
        "apps.uploads.scanning.Image.open",
        side_effect=Image.DecompressionBombError("oversized image"),
    )
    def test_decompression_bomb_is_quarantined(self, _image_open):
        safe, reason = inspect_upload_content(
            content=b"oversized-image",
            declared_mime_type="image/jpeg",
        )

        self.assertFalse(safe)
        self.assertEqual(reason, "image_decompression_bomb")

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

    def test_create_upload_requires_upload_action_scope(self):
        self.session.allowed_actions_json = ["session:read"]
        self.session.save(update_fields=["allowed_actions_json", "updated_at"])

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
            allowed_actions_json=list(VERIFICATION_SESSION_ACTIONS),
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
