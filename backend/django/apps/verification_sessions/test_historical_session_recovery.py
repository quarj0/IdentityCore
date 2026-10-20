from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.biometrics.models import LivenessChallenge, SelfieCapture
from apps.consent.test_helpers import accept_test_consent
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.risk.services import _document_requires_manual_review
from apps.uploads.models import UploadPurpose
from apps.verification_sessions import tests as fixtures
from apps.verifications.models import VerificationDecision


class HistoricalSessionRecoveryTests(APITestCase):
    setUp = fixtures.VerificationSessionPortalTests.setUp
    session_headers = fixtures.VerificationSessionPortalTests.session_headers
    create_upload = fixtures.VerificationSessionPortalTests.create_upload

    def document(self, status=IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED):
        accept_test_consent(self.verification)
        self.verification.status = "awaiting_selfie"
        self.verification.save(update_fields=["status", "updated_at"])
        return IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status=status,
            extracted_data_json={
                "document_classification": {
                    "requires_manual_review": True,
                    "issues": ["document_ocr_unavailable"],
                }
            },
        )

    def test_challenge_returns_server_relative_lifetime(self):
        accept_test_consent(self.verification)
        self.verification.policy_snapshot_json["required_liveness_level"] = "active"
        self.verification.save(update_fields=["policy_snapshot_json", "updated_at"])
        self.session.expires_at = timezone.now() + timedelta(seconds=45)
        self.session.save(update_fields=["expires_at", "updated_at"])
        response = self.client.post(
            reverse(
                "verification-session-liveness-challenge",
                kwargs={"session_id": self.session.public_id},
            ),
            {},
            format="json",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertGreater(response.data["data"]["expires_in"], 0)
        self.assertLessEqual(response.data["data"]["expires_in"], 45)
        self.assertIn("expires_at", response.data["data"])

    def test_review_flagged_document_can_submit_selfie(self):
        document = self.document()
        upload = self.create_upload(
            purpose=UploadPurpose.SELFIE_CAPTURE, suffix="REVIEW"
        )
        response = self.client.post(
            reverse(
                "verification-session-selfies",
                kwargs={"session_id": self.session.public_id},
            ),
            {"capture_type": "image", "upload_id": upload.public_id},
            format="json",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        document.refresh_from_db()
        self.assertEqual(document.status, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        self.assertTrue(
            _document_requires_manual_review(
                document.extracted_data_json["document_classification"]
            )
        )

    def test_unvalidated_documents_still_cannot_submit_selfie(self):
        document = self.document(status=IdentityDocumentStatus.PROCESSING)
        for index, status in enumerate(["processing", "rejected", "failed"]):
            with self.subTest(status=status):
                document.status = status
                document.save(update_fields=["status", "updated_at"])
                upload = self.create_upload(
                    purpose=UploadPurpose.SELFIE_CAPTURE, suffix=f"BAD{index}"
                )
                response = self.client.post(
                    reverse(
                        "verification-session-selfies",
                        kwargs={"session_id": self.session.public_id},
                    ),
                    {"capture_type": "image", "upload_id": upload.public_id},
                    format="json",
                    **self.session_headers(),
                )
                self.assertEqual(response.status_code, 400)
                upload.refresh_from_db()
                self.assertEqual(upload.status, "uploaded")
        self.assertFalse(self.verification.selfie_captures.exists())

    @patch("apps.biometrics.tasks.process_verification_biometrics_task.delay")
    def test_review_flagged_document_can_queue_active_liveness(self, publish):
        document = self.document()
        DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=document,
            side="front",
            storage_key="synthetic/document",
            mime_type="image/jpeg",
            status="uploaded",
            captured_at=timezone.now(),
        )
        capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            storage_key="synthetic/video",
            capture_type="video",
            mime_type="video/webm",
            status="uploaded",
            captured_at=timezone.now(),
        )
        challenge = LivenessChallenge.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            actions=[
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
            ],
            expires_at=timezone.now() + timedelta(minutes=2),
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse(
                    "verification-session-liveness",
                    kwargs={"session_id": self.session.public_id},
                ),
                {
                    "liveness_type": "active",
                    "selfie_capture_id": capture.public_id,
                    "challenge_id": challenge.public_id,
                },
                format="json",
                **self.session_headers(),
            )
        self.assertEqual(response.status_code, 200, response.data)
        publish.assert_called_once_with(response.data["data"]["liveness_check_id"])
        document.refresh_from_db()
        self.assertEqual(document.status, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        self.assertTrue(
            _document_requires_manual_review(
                document.extracted_data_json["document_classification"]
            )
        )
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )

    def test_unknown_configured_country_is_not_replaced_with_ghana(self):
        self.verification.metadata_json["country_code"] = "US"
        self.verification.save(update_fields=["metadata_json", "updated_at"])
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("country_code", response.data["error"]["details"])

    def test_missing_metadata_country_uses_organization_registration(self):
        self.organization.settings_json["onboarding"] = {
            "registration": {"organization_country": "NG"}
        }
        self.organization.save(update_fields=["settings_json", "updated_at"])
        self.verification.metadata_json.pop("country_code")
        self.verification.save(update_fields=["metadata_json", "updated_at"])
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["document"]["country_code"], "NG")

    def test_document_submission_requires_an_issuing_country(self):
        accept_test_consent(self.verification)
        self.verification.status = "in_progress"
        self.verification.save(update_fields=["status", "updated_at"])
        upload = self.create_upload(
            purpose=UploadPurpose.DOCUMENT_CAPTURE, suffix="COUNTRY"
        )
        response = self.client.post(
            reverse(
                "verification-session-documents",
                kwargs={"session_id": self.session.public_id},
            ),
            {
                "document_type": "passport",
                "captures": [{"side": "single", "upload_id": upload.public_id}],
            },
            format="json",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("country_code", response.data["error"]["details"])
        self.assertFalse(self.verification.identity_documents.exists())
        upload.refresh_from_db()
        self.assertEqual(upload.status, "uploaded")

    def test_review_flagged_document_status_displays_the_selfie_step(self):
        document = self.document()
        response = self.client.get(
            reverse(
                "verification-session-status",
                kwargs={"session_id": self.session.public_id},
            ),
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["current_step"], "selfie_capture")
        self.assertEqual(
            response.data["data"]["evidence"]["identity_document_id"],
            document.public_id,
        )
