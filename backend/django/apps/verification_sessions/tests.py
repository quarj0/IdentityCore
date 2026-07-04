from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.consent.models import ConsentRecord, ConsentTemplate, ConsentTemplateStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verifications.models import Verification, VerificationSession, VerificationStatus
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
