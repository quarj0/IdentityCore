import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.uploads.models import Upload, UploadStatus
from apps.uploads.provenance import capture_signals, issue_receipt, validate_receipt
from apps.uploads import tests as upload_tests
from apps.verification_sessions.serializers import resolve_session_upload
from apps.verifications.models import Verification, VerificationSession


class CaptureProvenanceTests(APITestCase):
    setUp = upload_tests.UploadCreateTests.setUp
    auth_headers = upload_tests.UploadCreateTests.auth_headers

    def _complete(self, method="camera"):
        output = io.BytesIO()
        Image.new("RGB", (32, 32), "green").save(output, "JPEG")
        content = output.getvalue()
        response = self.client.post(
            reverse("upload-create"),
            {
                "purpose": "document_capture",
                "mime_type": "image/jpeg",
                "file_size_bytes": len(content),
                "capture_method": method,
            },
            format="json",
            **self.auth_headers()
        )
        self.assertEqual(response.status_code, 201)
        upload_id = response.data["data"]["upload_id"]
        with patch("apps.uploads.views.put_object_bytes"):
            response = self.client.post(
                reverse("upload-transfer", kwargs={"upload_id": upload_id}),
                {
                    "file": SimpleUploadedFile(
                        "capture.jpg", content, content_type="image/jpeg"
                    ),
                },
                format="multipart",
                **self.auth_headers()
            )
        self.assertEqual(response.status_code, 200)
        return Upload.objects.get(public_id=upload_id)

    def test_validated_media_receipt_binds_ownership_and_digest(self):
        upload = self._complete()
        self.assertEqual(upload.capture_provenance_version, 1)
        self.assertTrue(validate_receipt(upload))
        for attribute, changed in (
            ("checksum_sha256", "a" * 64),
            ("purpose", "selfie_capture"),
            ("verification_session_id", 987654),
            ("tenant_id", 987654),
            ("capture_method", "file"),
        ):
            original = getattr(upload, attribute)
            setattr(upload, attribute, changed)
            with self.assertRaises(ValidationError):
                validate_receipt(upload)
            setattr(upload, attribute, original)

    def test_altered_and_stripped_receipts_reject_submission(self):
        upload = self._complete()
        for receipt in (upload.capture_receipt + "altered", ""):
            Upload.objects.filter(pk=upload.pk).update(capture_receipt=receipt)
            with self.assertRaises(ValidationError):
                resolve_session_upload(
                    verification_session=self.session,
                    upload_id=upload.public_id,
                    purpose="document_capture",
                )

    def test_same_upload_retry_preserves_signed_receipt(self):
        upload = self._complete()
        before = upload.capture_receipt
        response = self.client.post(
            reverse("upload-complete", kwargs={"upload_id": upload.public_id}),
            {},
            format="json",
            **self.auth_headers()
        )
        self.assertEqual(response.status_code, 200)
        upload.refresh_from_db()
        self.assertEqual(upload.capture_receipt, before)
        self.assertTrue(validate_receipt(upload))

    def test_fallback_is_explicit_and_client_camera_claim_is_untrusted(self):
        upload = self._complete("file")
        upload.status = UploadStatus.CONSUMED
        from django.utils import timezone

        upload.consumed_at = timezone.now()
        upload.save()
        signals = capture_signals(self.verification)
        self.assertEqual(signals["file_fallback"], 1)
        self.assertEqual(signals["attested"], 1)
        self.assertFalse(signals["client_metadata_trusted"])
        self.assertNotIn(upload.checksum_sha256, str(signals))

    def test_reuse_is_flagged_only_across_live_cases_in_same_tenant(self):
        upload = self._complete()
        from django.utils import timezone

        upload.status = UploadStatus.CONSUMED
        upload.consumed_at = timezone.now()
        upload.save()
        self.assertEqual(capture_signals(self.verification)["media_reuse"], 0)
        other_case = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Another case",
            expires_at=self.verification.expires_at,
        )
        other_session = VerificationSession(
            tenant=self.tenant,
            verification=other_case,
            expires_at=other_case.expires_at,
        )
        other_session.set_session_token("other-case-token")
        other_session.save()
        other = Upload.objects.create(
            tenant=self.tenant,
            verification=other_case,
            verification_session=other_session,
            purpose=upload.purpose,
            storage_key="another-media",
            mime_type=upload.mime_type,
            file_size_bytes=upload.file_size_bytes,
            checksum_sha256=upload.checksum_sha256,
            status=UploadStatus.UPLOADED,
            expires_at=upload.expires_at,
        )
        self.assertEqual(capture_signals(self.verification)["media_reuse"], 1)
        # A foreign-tenant copy cannot create or expose a tenant correlation.
        Upload.objects.filter(pk=other.pk).update(tenant_id=self._foreign_tenant().pk)
        self.assertEqual(capture_signals(self.verification)["media_reuse"], 0)
        Upload.objects.filter(pk=other.pk).update(
            tenant=self.tenant, deleted_at=timezone.now()
        )
        self.assertEqual(capture_signals(self.verification)["media_reuse"], 0)

    def _foreign_tenant(self):
        from apps.tenants.models import Tenant
        from apps.organizations.models import Organization

        organization = Organization.objects.create(name="Foreign", slug="foreign")
        return Tenant.objects.create(
            organization=organization, name="Foreign", slug="foreign"
        )

    def test_legacy_evidence_remains_explicitly_unverified(self):
        upload = self._complete()
        upload.capture_receipt = ""
        upload.capture_provenance_version = 0
        upload.save(update_fields=["capture_provenance_version", "capture_receipt"])
        from importlib import import_module
        from django.apps import apps
        from django.db import connection
        from types import SimpleNamespace

        migration = import_module(
            "apps.uploads.migrations.0006_upload_capture_method_upload_capture_receipt"
        )
        migration.enroll_legacy_uploads(apps, SimpleNamespace(connection=connection))
        upload.refresh_from_db()
        self.assertTrue(upload.capture_receipt)
        self.assertFalse(validate_receipt(upload))
        upload.checksum_sha256 = "b" * 64
        with self.assertRaises(ValidationError):
            validate_receipt(upload)

    def test_downgrading_new_upload_to_legacy_is_invalid(self):
        upload = self._complete()
        Upload.objects.filter(pk=upload.pk).update(
            capture_receipt="", capture_provenance_version=0
        )
        with self.assertRaises(ValidationError):
            resolve_session_upload(
                verification_session=self.session,
                upload_id=upload.public_id,
                purpose="document_capture",
            )
        from django.utils import timezone

        Upload.objects.filter(pk=upload.pk).update(
            status=UploadStatus.CONSUMED, consumed_at=timezone.now()
        )
        self.assertEqual(capture_signals(self.verification)["invalid"], 1)
        self.assertEqual(capture_signals(self.verification)["legacy_unverified"], 0)

    def test_unsupported_receipt_version_is_rejected(self):
        upload = self._complete()
        upload.capture_provenance_version = 2
        with self.assertRaises(ValidationError):
            validate_receipt(upload)

    def test_receipt_from_another_upload_is_invalid(self):
        upload = self._complete()
        another = self._complete()
        upload.capture_receipt = issue_receipt(another)
        with self.assertRaises(ValidationError):
            validate_receipt(upload)
