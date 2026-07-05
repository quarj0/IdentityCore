from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.biometrics.models import FaceMatch, LivenessCheck, SelfieCapture
from apps.consent.models import ConsentRecord, ConsentTemplate, ConsentTemplateStatus
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.providers.models import ProviderCheck
from apps.risk.models import RiskAssessment
from apps.tenants.models import Tenant
from apps.verifications.models import Verification, VerificationDecision, VerificationSession, VerificationStatus
from apps.verification_subjects.models import VerificationSubject


class VerificationSessionPortalTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Example Bank",
            slug="example-bank",
            settings_json={"logo_url": "https://cdn.example.com/logo.png"},
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Example Bank Tenant",
            slug="example-bank-tenant",
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
            email="akosua@example.com",
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

    def session_headers(self, token=None):
        return {
            "HTTP_AUTHORIZATION": f"Bearer {token or self.raw_session_token}",
            "HTTP_USER_AGENT": "PortalBrowser/1.0",
            "HTTP_X_DEVICE_FINGERPRINT": "device-123",
            "REMOTE_ADDR": "127.0.0.1",
        }

    def test_get_session_returns_portal_context_and_activates_session(self):
        response = self.client.get(
            reverse("verification-session-detail", kwargs={"session_id": self.session.public_id}),
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "active")
        self.assertIsNotNone(self.session.started_at)
        self.assertEqual(response.data["data"]["session_id"], self.session.public_id)
        self.assertEqual(response.data["data"]["organization"]["name"], self.organization.name)
        self.assertEqual(
            response.data["data"]["required_steps"],
            ["consent", "document_capture", "selfie_capture", "liveness_check"],
        )

    def test_get_session_rejects_invalid_token(self):
        response = self.client.get(
            reverse("verification-session-detail", kwargs={"session_id": self.session.public_id}),
            **self.session_headers(token="wrong-token"),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_session_is_rejected_and_marked_expired(self):
        self.session.expires_at = timezone.now() - timedelta(minutes=1)
        self.session.save(update_fields=["expires_at", "updated_at"])

        response = self.client.get(
            reverse("verification-session-detail", kwargs={"session_id": self.session.public_id}),
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "expired")

    def test_accept_consent_creates_record_and_advances_verification(self):
        ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Standard Verification Consent",
            version=1,
            language="en",
            content="I consent to identity verification.",
            status=ConsentTemplateStatus.ACTIVE,
            created_by=self.user,
        )

        response = self.client.post(
            reverse("verification-session-consent", kwargs={"session_id": self.session.public_id}),
            {"accepted": True},
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["next_step"], "document_capture")
        self.verification.refresh_from_db()
        self.session.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.IN_PROGRESS)
        self.assertEqual(self.session.status, "active")
        consent_record = ConsentRecord.objects.get(public_id=response.data["data"]["consent_record_id"])
        self.assertEqual(consent_record.consent_template.content, "I consent to identity verification.")
        self.assertEqual(consent_record.device_fingerprint, "device-123")

    def test_accept_consent_requires_true(self):
        response = self.client.post(
            reverse("verification-session-consent", kwargs={"session_id": self.session.public_id}),
            {"accepted": False},
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_documents_requires_consent(self):
        response = self.client.post(
            reverse("verification-session-documents", kwargs={"session_id": self.session.public_id}),
            {
                "document_type": "national_id",
                "country_code": "GH",
                "captures": [{"side": "front", "upload_id": "upl_01JABC"}],
            },
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.verification_sessions.views.process_identity_document_task.delay")
    def test_submit_documents_creates_identity_document_and_captures(self, mock_delay):
        ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            consent_text_snapshot="I consent to identity verification.",
            accepted=True,
            accepted_at=timezone.now(),
        )
        self.verification.status = VerificationStatus.IN_PROGRESS
        self.verification.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            reverse("verification-session-documents", kwargs={"session_id": self.session.public_id}),
            {
                "document_type": "national_id",
                "country_code": "GH",
                "captures": [
                    {"side": "front", "upload_id": "upl_01JABC"},
                    {"side": "back", "upload_id": "upl_01JABD"},
                ],
            },
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "processing")
        self.assertEqual(response.data["data"]["next_step"], "selfie_capture")
        identity_document = IdentityDocument.objects.get(public_id=response.data["data"]["identity_document_id"])
        self.assertEqual(identity_document.document_type_id, "national_id")
        self.assertEqual(identity_document.country_profile_id, "GH")
        self.assertEqual(identity_document.status, "processing")
        self.assertEqual(identity_document.captures.count(), 2)
        self.assertSetEqual(
            set(identity_document.captures.values_list("side", flat=True)),
            {"front", "back"},
        )
        capture = DocumentCapture.objects.get(identity_document=identity_document, side="front")
        self.assertEqual(capture.storage_key, "uploads/documents/upl_01JABC")
        self.assertTrue(
            ProviderCheck.objects.filter(
                verification=self.verification,
                check_type="document_ocr",
            ).exists()
        )
        mock_delay.assert_called_once_with(identity_document.public_id)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.AWAITING_SELFIE)

    def test_submit_documents_rejects_duplicate_sides(self):
        ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            consent_text_snapshot="I consent to identity verification.",
            accepted=True,
            accepted_at=timezone.now(),
        )

        response = self.client.post(
            reverse("verification-session-documents", kwargs={"session_id": self.session.public_id}),
            {
                "document_type": "passport",
                "captures": [
                    {"side": "front", "upload_id": "upl_01JABC"},
                    {"side": "front", "upload_id": "upl_01JABD"},
                ],
            },
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_selfie_requires_document_submission(self):
        ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            consent_text_snapshot="I consent to identity verification.",
            accepted=True,
            accepted_at=timezone.now(),
        )

        response = self.client.post(
            reverse("verification-session-selfies", kwargs={"session_id": self.session.public_id}),
            {"capture_type": "image", "upload_id": "upl_01JSELFIE"},
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_selfie_creates_capture_and_advances_next_step(self):
        ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            consent_text_snapshot="I consent to identity verification.",
            accepted=True,
            accepted_at=timezone.now(),
        )
        IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processing",
        )
        self.verification.status = VerificationStatus.AWAITING_SELFIE
        self.verification.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            reverse("verification-session-selfies", kwargs={"session_id": self.session.public_id}),
            {"capture_type": "image", "upload_id": "upl_01JSELFIE"},
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "processing")
        self.assertEqual(response.data["data"]["next_step"], "liveness_check")
        selfie_capture = SelfieCapture.objects.get(public_id=response.data["data"]["selfie_capture_id"])
        self.assertEqual(selfie_capture.capture_type, "image")
        self.assertEqual(selfie_capture.storage_key, "uploads/selfies/upl_01JSELFIE")
        self.assertEqual(selfie_capture.status, "uploaded")
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.PROCESSING)

    def test_submit_liveness_requires_matching_selfie_capture(self):
        response = self.client.post(
            reverse("verification-session-liveness", kwargs={"session_id": self.session.public_id}),
            {"liveness_type": "passive", "selfie_capture_id": "sel_missing"},
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.verification_sessions.views.process_verification_biometrics_task.delay")
    def test_submit_liveness_creates_provider_checks_and_queues_background_processing(self, mock_delay):
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processing",
        )
        document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/upl_01JABC",
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=0,
            checksum_sha256="",
            status="uploaded",
            captured_at=timezone.now(),
        )
        selfie_capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/upl_01JSELFIE",
            storage_provider="local",
            capture_type="image",
            mime_type="image/jpeg",
            file_size_bytes=0,
            checksum_sha256="",
            face_count=1,
            status="uploaded",
            captured_at=timezone.now(),
        )
        self.verification.status = VerificationStatus.PROCESSING
        self.verification.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            reverse("verification-session-liveness", kwargs={"session_id": self.session.public_id}),
            {"liveness_type": "passive", "selfie_capture_id": selfie_capture.public_id},
            format="json",
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "processing")
        liveness_check = LivenessCheck.objects.get(public_id=response.data["data"]["liveness_check_id"])
        self.assertEqual(liveness_check.selfie_capture, selfie_capture)
        self.assertEqual(liveness_check.liveness_type, "passive")
        self.assertEqual(liveness_check.status, "inconclusive")
        self.assertTrue(liveness_check.provider_check_id.startswith("pck_"))
        face_match = FaceMatch.objects.get(verification=self.verification, selfie_capture=selfie_capture)
        self.assertEqual(face_match.identity_document, identity_document)
        self.assertEqual(face_match.document_capture, document_capture)
        self.assertEqual(face_match.status, "inconclusive")
        self.assertTrue(face_match.provider_check_id.startswith("pck_"))
        self.assertEqual(ProviderCheck.objects.filter(verification=self.verification).count(), 2)
        self.assertFalse(RiskAssessment.objects.filter(verification=self.verification).exists())
        self.assertFalse(VerificationDecision.objects.filter(verification=self.verification).exists())
        self.assertFalse(Notification.objects.filter(tenant=self.tenant).exists())
        mock_delay.assert_called_once_with(liveness_check.public_id)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.PROCESSING)

    def test_get_session_status_for_pending_consent(self):
        response = self.client.get(
            reverse("verification-session-status", kwargs={"session_id": self.session.public_id}),
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["verification_id"], self.verification.public_id)
        self.assertEqual(response.data["data"]["status"], VerificationStatus.PENDING_CONSENT)
        self.assertEqual(response.data["data"]["current_step"], "consent")

    def test_get_session_status_for_processing(self):
        self.verification.status = VerificationStatus.PROCESSING
        self.verification.save(update_fields=["status", "updated_at"])

        response = self.client.get(
            reverse("verification-session-status", kwargs={"session_id": self.session.public_id}),
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], VerificationStatus.PROCESSING)
        self.assertEqual(response.data["data"]["current_step"], "processing")
        self.assertEqual(response.data["data"]["message"], "Your verification is being processed.")

    def test_get_session_status_for_verified(self):
        self.verification.status = VerificationStatus.VERIFIED
        self.verification.save(update_fields=["status", "updated_at"])

        response = self.client.get(
            reverse("verification-session-status", kwargs={"session_id": self.session.public_id}),
            **self.session_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], VerificationStatus.VERIFIED)
        self.assertEqual(response.data["data"]["current_step"], "completed")
