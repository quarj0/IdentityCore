from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.identity_documents.tasks import process_identity_document_task
from apps.organizations.models import Organization
from apps.providers.models import Provider, ProviderCheck, ProviderCheckStatus, ProviderType
from apps.tenants.models import Tenant
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class IdentityDocumentTaskTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Kwame Mensah",
            email="kwame@example.com",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding",
            status=VerificationStatus.AWAITING_SELFIE,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status=IdentityDocumentStatus.PROCESSING,
        )
        self.capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=self.identity_document,
            side="front",
            storage_key="uploads/documents/doc_good",
            captured_at=timezone.now(),
        )
        self.upload = Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.verification.sessions.create(
                tenant=self.tenant,
                session_token_hash="placeholder",
                expires_at=timezone.now() + timedelta(hours=1),
            ),
            purpose=UploadPurpose.DOCUMENT_CAPTURE,
            storage_key=self.capture.storage_key,
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            status=UploadStatus.CONSUMED,
            expires_at=timezone.now() + timedelta(minutes=10),
            consumed_at=timezone.now(),
        )
        self.provider = Provider.objects.create(
            name="Internal OCR Engine",
            code="internal-ocr-test",
            provider_type=ProviderType.DOCUMENT,
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=self.provider,
            check_type="document_ocr",
            status=ProviderCheckStatus.PENDING,
            request_metadata_json={"identity_document_id": self.identity_document.public_id},
            started_at=timezone.now(),
        )

    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_marks_document_processed(self, mock_quality, mock_ocr):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.88, "issues": []}
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.91,
            "extracted_fields": {"full_name": "Kwame Mensah"},
            "model_name": "mock-ocr",
            "model_version": "v1",
        }

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.PROCESSED)
        self.identity_document.refresh_from_db()
        self.capture.refresh_from_db()
        self.upload.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.PROCESSED)
        self.assertEqual(self.capture.status, "validated")
        self.assertEqual(self.upload.status, UploadStatus.PROMOTED)
        self.assertEqual(self.identity_document.extracted_data_json["full_name"], "Kwame Mensah")
        self.assertEqual(mock_quality.call_args.kwargs["document_storage_bucket"], "")
        self.assertEqual(mock_ocr.call_args.kwargs["document_storage_bucket"], "")

    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_marks_document_rejected_when_quality_fails(self, mock_quality, mock_ocr):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.42, "issues": ["blur_detected"]}
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.91,
            "extracted_fields": {"full_name": "Kwame Mensah"},
            "model_name": "mock-ocr",
            "model_version": "v1",
        }

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.REJECTED)
        self.identity_document.refresh_from_db()
        self.capture.refresh_from_db()
        self.upload.refresh_from_db()
        self.assertEqual(self.capture.status, "rejected")
        self.assertEqual(self.upload.status, UploadStatus.PROMOTED)
