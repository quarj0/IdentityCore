from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.identity_documents.tasks import process_identity_document_task
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderType,
)
from apps.providers.ai_service import AIServiceUnavailable
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
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=self.provider,
            check_type=ProviderCheckType.DOCUMENT_CLASSIFICATION,
            status=ProviderCheckStatus.PENDING,
            request_metadata_json={"identity_document_id": self.identity_document.public_id},
            started_at=timezone.now(),
        )

    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_marks_document_processed(
        self, mock_quality, mock_ocr, mock_classification
    ):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.88, "issues": []}
        mock_classification.return_value = {
            "status": "completed",
            "classification_status": "recognized",
            "predicted_document_type": "national_id",
            "expected_document_type": "national_id",
            "matched_expected_document_type": True,
            "predicted_country_code": "GH",
            "confidence_score": 0.95,
            "evidence_score": 0.95,
            "classification_margin": 0.95,
            "workflow_action": "continue",
            "requires_manual_review": False,
            "manual_review": {
                "required": False,
                "priority": "low",
                "reason_codes": [],
                "review_category": "document_classification",
            },
            "issues": [],
            "ocr": {"average_confidence": 0.95, "line_count": 2},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
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
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_SELFIE)
        self.assertEqual(self.capture.status, "validated")
        self.assertEqual(self.upload.status, UploadStatus.PROMOTED)
        self.assertEqual(self.identity_document.extracted_data_json["full_name"], "Kwame Mensah")
        self.assertIn(
            "document_classification", self.identity_document.extracted_data_json
        )
        self.assertEqual(
            self.identity_document.extracted_data_json["document_classification"][
                "classification_status"
            ],
            "recognized",
        )
        self.assertEqual(mock_quality.call_args.kwargs["document_storage_bucket"], "")
        self.assertEqual(
            mock_classification.call_args.kwargs["document_storage_bucket"], ""
        )
        self.assertEqual(mock_ocr.call_args.kwargs["document_storage_bucket"], "")

    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_routes_manual_review_signals(
        self, mock_quality, mock_ocr, mock_classification
    ):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.88, "issues": []}
        mock_classification.return_value = {
            "status": "completed",
            "classification_status": "unknown",
            "predicted_document_type": "unknown",
            "predicted_country_code": None,
            "expected_document_type": "national_id",
            "matched_expected_document_type": None,
            "confidence_score": 0.0,
            "evidence_score": 0.0,
            "classification_margin": 0.0,
            "workflow_action": "continue_with_review",
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "high",
                "reason_codes": ["document_media_missing"],
                "review_category": "document_classification",
            },
            "issues": ["document_media_missing"],
            "ocr": {"average_confidence": 0.0, "line_count": 0},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.0,
            "extracted_fields": {},
            "raw_text_lines": [],
            "model_name": "mock-ocr",
            "model_version": "v1",
        }

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual(
            self.identity_document.status,
            IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_SELFIE)
        self.assertEqual(
            self.identity_document.extracted_data_json["document_classification"][
                "workflow_action"
            ],
            "continue_with_review",
        )

    @patch("apps.identity_documents.tasks.promote_upload_to_media_by_storage_key")
    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_keeps_processing_when_promotion_fails(
        self, mock_quality, mock_ocr, mock_classification, mock_promote
    ):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.88, "issues": []}
        mock_classification.return_value = {
            "status": "completed",
            "classification_status": "recognized",
            "predicted_document_type": "national_id",
            "expected_document_type": "national_id",
            "matched_expected_document_type": True,
            "predicted_country_code": "GH",
            "confidence_score": 0.95,
            "evidence_score": 0.95,
            "classification_margin": 0.95,
            "workflow_action": "continue",
            "requires_manual_review": False,
            "manual_review": {
                "required": False,
                "priority": "low",
                "reason_codes": [],
                "review_category": "document_classification",
            },
            "issues": [],
            "ocr": {"average_confidence": 0.95, "line_count": 2},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.91,
            "extracted_fields": {"full_name": "Kwame Mensah"},
            "model_name": "mock-ocr",
            "model_version": "v1",
        }
        mock_promote.side_effect = RuntimeError("storage unavailable")

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.PROCESSED)
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.upload.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.PROCESSED)
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_SELFIE)
        self.assertEqual(self.upload.status, UploadStatus.CONSUMED)

    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_routes_classification_outage_to_manual_review(
        self, mock_quality, mock_classification, mock_ocr
    ):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.88, "issues": []}
        mock_classification.side_effect = AIServiceUnavailable("classification unavailable")
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.91,
            "extracted_fields": {"full_name": "Kwame Mensah"},
            "model_name": "mock-ocr",
            "model_version": "v1",
        }

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.upload.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.PROCESSED)
        self.assertEqual(
            self.verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        self.assertEqual(self.upload.status, UploadStatus.PROMOTED)

    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_keeps_moving_when_quality_processing_fails(
        self, mock_quality, mock_ocr, mock_classification
    ):
        mock_quality.side_effect = RuntimeError("quality unavailable")
        mock_classification.return_value = {
            "status": "completed",
            "classification_status": "recognized",
            "predicted_document_type": "national_id",
            "expected_document_type": "national_id",
            "matched_expected_document_type": True,
            "predicted_country_code": "GH",
            "confidence_score": 0.95,
            "evidence_score": 0.95,
            "classification_margin": 0.95,
            "workflow_action": "continue",
            "requires_manual_review": False,
            "manual_review": {
                "required": False,
                "priority": "low",
                "reason_codes": [],
                "review_category": "document_classification",
            },
            "issues": [],
            "ocr": {"average_confidence": 0.95, "line_count": 2},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
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
        self.verification.refresh_from_db()
        self.upload.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.PROCESSED)
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_SELFIE)
        self.assertEqual(self.upload.status, UploadStatus.PROMOTED)

    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_task_marks_document_rejected_when_quality_fails(
        self, mock_quality, mock_ocr, mock_classification
    ):
        mock_quality.return_value = {"status": "completed", "quality_score": 0.42, "issues": ["blur_detected"]}
        mock_classification.return_value = {
            "status": "completed",
            "predicted_document_type": "national_id",
            "expected_document_type": "national_id",
            "matched_expected_document_type": True,
            "confidence_score": 0.95,
            "issues": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
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
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_DOCUMENT)

    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_continues_for_unknown_classification(
        self, mock_quality, mock_ocr, mock_classification
    ):
        mock_quality.return_value = {
            "status": "completed",
            "quality_score": 0.91,
            "issues": [],
        }
        mock_classification.return_value = {
            "status": "completed",
            "classification_status": "unknown",
            "predicted_document_type": "unknown",
            "expected_document_type": "national_id",
            "matched_expected_document_type": None,
            "predicted_country_code": None,
            "confidence_score": 0.0,
            "evidence_score": 0.0,
            "classification_margin": 0.0,
            "workflow_action": "continue_with_review",
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "normal",
                "reason_codes": ["document_type_not_determined"],
                "review_category": "document_classification",
            },
            "issues": ["document_type_not_determined"],
            "ocr": {"average_confidence": 0.0, "line_count": 0},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.0,
            "extracted_fields": {},
            "model_name": "mock-ocr",
            "model_version": "v1",
        }

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.PROCESSED)
        self.assertEqual(
            self.verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )

    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_process_identity_document_continues_for_mismatch_classification(
        self, mock_quality, mock_ocr, mock_classification
    ):
        mock_quality.return_value = {
            "status": "completed",
            "quality_score": 0.91,
            "issues": [],
        }
        mock_classification.return_value = {
            "status": "completed",
            "classification_status": "recognized",
            "predicted_document_type": "passport",
            "expected_document_type": "national_id",
            "matched_expected_document_type": False,
            "predicted_country_code": "GH",
            "confidence_score": 0.95,
            "evidence_score": 0.95,
            "classification_margin": 0.55,
            "workflow_action": "continue_with_review",
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "high",
                "reason_codes": ["document_type_mismatch"],
                "review_category": "document_classification",
            },
            "issues": ["document_type_mismatch"],
            "ocr": {"average_confidence": 0.95, "line_count": 2},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "mock-document-classifier",
            "model_version": "v1",
        }
        mock_ocr.return_value = {
            "status": "completed",
            "confidence_score": 0.91,
            "extracted_fields": {"full_name": "Kwame Mensah"},
            "model_name": "mock-ocr",
            "model_version": "v1",
        }

        result = process_identity_document_task(self.identity_document.public_id)

        self.assertEqual(result, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual(self.identity_document.status, IdentityDocumentStatus.PROCESSED)
        self.assertEqual(
            self.verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
