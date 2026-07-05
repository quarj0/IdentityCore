from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.access_control.models import Permission, Role, RolePermission, RoleScope
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.biometrics.models import SelfieCapture
from apps.consent.models import ConsentRecord, ConsentTemplate, ConsentTemplateStatus
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
)
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderType,
)
from apps.risk.models import RiskAssessment
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class ManagementAPIEndpointTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme", slug="acme-management"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Management Tenant",
            slug="acme-management-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="manager@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": "StrongPassword123!"},
            format="json",
        )
        access = login_response.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Akosua Owusu",
            email="akosua@example.com",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Verification flow",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_access_control_endpoints_return_roles_and_permissions(self):
        role = Role.objects.create(
            tenant=self.tenant,
            name="Officer",
            scope=RoleScope.TENANT,
            status="active",
        )
        permission = Permission.objects.create(
            code="view_verification",
            name="View verification",
        )
        RolePermission.objects.create(role=role, permission=permission)

        roles_response = self.client.get(reverse("role-list"))
        permissions_response = self.client.get(reverse("permission-list"))

        self.assertEqual(roles_response.status_code, status.HTTP_200_OK)
        self.assertEqual(permissions_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            roles_response.data["data"]["results"][0]["permission_codes"],
            ["view_verification"],
        )
        self.assertEqual(
            permissions_response.data["data"]["results"][0]["code"], "view_verification"
        )

    def test_consent_notification_org_tenant_and_provider_endpoints_return_data(self):
        consent_template = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Standard Consent",
            version=1,
            language="en",
            content="I consent",
            status=ConsentTemplateStatus.ACTIVE,
            created_by=self.user,
        )
        ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            consent_template=consent_template,
            consent_text_snapshot="I consent",
            accepted=True,
            accepted_at=timezone.now(),
        )
        Notification.objects.create(
            tenant=self.tenant,
            recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
            recipient="akosua@example.com",
            channel=NotificationChannel.EMAIL,
            template_code="verification.created",
            subject="Verification",
            body_preview="Verification link",
        )
        provider = Provider.objects.create(
            name="Internal Liveness Engine",
            code="internal-liveness-test",
            provider_type=ProviderType.LIVENESS,
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            normalized_result_json={"status": "passed"},
        )
        RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            risk_score="14.00",
            risk_level="low",
            recommendation="approve",
            signals_json={"document_submitted": True},
        )

        self.assertEqual(
            self.client.get(reverse("consent-template-list")).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(reverse("consent-record-list")).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(reverse("notification-list")).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(reverse("organization-detail")).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(reverse("tenant-detail")).status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            self.client.get(reverse("provider-list")).status_code, status.HTTP_200_OK
        )
        provider_checks_response = self.client.get(reverse("provider-check-list"))
        risk_response = self.client.get(reverse("risk-assessment-list"))

        self.assertEqual(provider_checks_response.status_code, status.HTTP_200_OK)
        self.assertEqual(risk_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            provider_checks_response.data["data"]["results"][0]["provider_code"],
            provider.code,
        )
        self.assertEqual(risk_response.data["data"]["results"][0]["risk_level"], "low")

    def test_media_download_url_endpoints_return_temporary_links(self):
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            status="processed",
        )
        document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/doc_123",
            captured_at=timezone.now(),
        )
        selfie_capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/selfie_123",
            capture_type="image",
            captured_at=timezone.now(),
        )

        document_response = self.client.get(
            reverse(
                "document-capture-download-url",
                kwargs={"capture_id": document_capture.public_id},
            )
        )
        selfie_response = self.client.get(
            reverse(
                "selfie-capture-download-url",
                kwargs={"selfie_id": selfie_capture.public_id},
            )
        )

        self.assertEqual(document_response.status_code, status.HTTP_200_OK)
        self.assertEqual(selfie_response.status_code, status.HTTP_200_OK)
        self.assertIn("download_url", document_response.data["data"])
        self.assertIn("download_url", selfie_response.data["data"])
