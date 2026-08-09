import json
from datetime import timedelta
from unittest.mock import patch

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
    ProviderCircuitState,
    ProviderCircuitStatus,
    ProviderRoute,
    ProviderRouteEnvironment,
    ProviderRouteStep,
    ProviderStatus,
    ProviderType,
)
from apps.providers.health import provider_health_scope
from apps.providers.services import publish_provider_route
from apps.projects.models import Project, ProjectEnvironment
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

    def test_provider_health_is_scoped_redacted_and_includes_route_circuit_state(self):
        provider = Provider.objects.create(
            name="Document Provider",
            code="document-health-provider",
            provider_type=ProviderType.DOCUMENT,
            configuration_json={"api_key": "never-return-this-secret"},
        )
        now = timezone.now()
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            request_metadata_json={"subject_email": "private@example.com"},
            response_metadata_json={"document_number": "GHA-PRIVATE-123"},
            normalized_result_json={"full_name": "Private Person"},
            started_at=now - timedelta(milliseconds=120),
            completed_at=now,
            duration_ms=120,
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.TIMEOUT,
            error_code="private@example.com",
            error_message="Private upstream response",
            started_at=now - timedelta(milliseconds=450),
            completed_at=now,
            duration_ms=450,
        )

        production_project = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production-health",
            environment=ProjectEnvironment.PRODUCTION,
            created_by=self.user,
        )
        production_verification = Verification.objects.create(
            tenant=self.tenant,
            project=production_project,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Production health isolation",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=production_verification,
            provider=provider,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            duration_ms=5,
        )

        other_organization = Organization.objects.create(
            name="Other Health Organization",
            slug="other-health-organization",
        )
        other_tenant = Tenant.objects.create(
            organization=other_organization,
            name="Other Health Tenant",
            slug="other-health-tenant",
            status="active",
        )
        other_subject = VerificationSubject.objects.create(
            tenant=other_tenant,
            full_name="Foreign Private Person",
            email="foreign-private@example.com",
        )
        other_verification = Verification.objects.create(
            tenant=other_tenant,
            organization=other_organization,
            verification_subject=other_subject,
            purpose="Tenant health isolation",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        ProviderCheck.objects.create(
            tenant=other_tenant,
            verification=other_verification,
            provider=provider,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            response_metadata_json={"email": "foreign-private@example.com"},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )

        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="document-health",
            name="Document health",
            environment=ProviderRouteEnvironment.SANDBOX,
            capability=ProviderCheckType.DOCUMENT_OCR,
        )
        step = ProviderRouteStep.objects.create(
            route=route,
            provider=provider,
            position=1,
        )
        publish_provider_route(route)
        ProviderCircuitState.objects.create(
            route_step=step,
            status=ProviderCircuitStatus.OPEN,
            consecutive_failures=3,
            opened_at=now,
            retry_after=now + timedelta(minutes=1),
        )

        response = self.client.get(
            reverse("provider-health"),
            {"environment": "sandbox", "window_hours": 24},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        health = response.data["data"]
        self.assertEqual(health["scope"]["tenant_id"], self.tenant.public_id)
        self.assertEqual(health["scope"]["environment"], "sandbox")
        self.assertEqual(health["providers"][0]["total_attempts"], 2)
        self.assertEqual(health["providers"][0]["availability_percent"], 50.0)
        self.assertEqual(health["providers"][0]["latency_ms"]["p95"], 450)
        self.assertEqual(
            health["providers"][0]["error_codes"],
            [{"code": "provider_error", "count": 1}],
        )
        self.assertEqual(health["routes"][0]["status"], "unavailable")
        self.assertEqual(health["routes"][0]["steps"][0]["circuit_status"], "open")
        serialized = json.dumps(health)
        for private_value in (
            "never-return-this-secret",
            "private@example.com",
            "GHA-PRIVATE-123",
            "Private Person",
            "Private upstream response",
            "foreign-private@example.com",
        ):
            self.assertNotIn(private_value, serialized)
        for private_key in (
            "configuration",
            "request_metadata",
            "response_metadata",
            "normalized_result",
            "error_message",
        ):
            self.assertNotIn(private_key, serialized)

    def test_provider_health_requires_a_valid_explicit_scope(self):
        self.assertEqual(
            self.client.get(reverse("provider-health")).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_provider_filtered_health_keeps_full_capability_specific_route(self):
        primary = Provider.objects.create(
            name="Primary health provider",
            code="primary-health-provider",
            provider_type=ProviderType.DOCUMENT,
        )
        fallback = Provider.objects.create(
            name="Fallback health provider",
            code="fallback-health-provider",
            provider_type=ProviderType.DOCUMENT,
        )
        now = timezone.now()
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=primary,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            duration_ms=10,
        )
        ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=primary,
            check_type=ProviderCheckType.DOCUMENT_QUALITY,
            status=ProviderCheckStatus.TIMEOUT,
            error_code="provider_timeout",
            started_at=now,
            completed_at=now,
            duration_ms=20,
        )
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="quality-health",
            name="Quality health",
            environment=ProviderRouteEnvironment.SANDBOX,
            capability=ProviderCheckType.DOCUMENT_QUALITY,
        )
        primary_step = ProviderRouteStep.objects.create(
            route=route, provider=primary, position=1
        )
        ProviderRouteStep.objects.create(route=route, provider=fallback, position=2)
        publish_provider_route(route)
        ProviderCircuitState.objects.create(
            route_step=primary_step,
            status=ProviderCircuitStatus.OPEN,
            consecutive_failures=3,
            retry_after=now - timedelta(seconds=1),
        )

        with patch(
            "common.fields.EncryptedJSONField.from_db_value",
            side_effect=AssertionError("health must not decrypt payload fields"),
        ):
            snapshot = provider_health_scope(
                tenant=self.tenant,
                environment="sandbox",
                provider_id=primary.public_id,
            )

        self.assertEqual(len(snapshot["providers"]), 1)
        self.assertEqual(len(snapshot["routes"]), 1)
        self.assertEqual(len(snapshot["routes"][0]["steps"]), 2)
        self.assertEqual(snapshot["routes"][0]["steps"][0]["health"], "unavailable")
        self.assertEqual(
            snapshot["routes"][0]["steps"][0]["circuit_status"], "half_open"
        )
        self.assertEqual(snapshot["routes"][0]["status"], "degraded")

        fallback.status = ProviderStatus.DISABLED
        fallback.save(update_fields=["status", "updated_at"])
        circuit = primary_step.circuit_state
        circuit.retry_after = now + timedelta(minutes=1)
        circuit.save(update_fields=["retry_after", "updated_at"])
        unavailable = provider_health_scope(
            tenant=self.tenant,
            environment="sandbox",
            provider_id=primary.public_id,
        )
        self.assertEqual(unavailable["routes"][0]["status"], "unavailable")
        self.assertEqual(
            self.client.get(
                reverse("provider-health"),
                {"environment": "sandbox", "window_hours": 0},
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

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
