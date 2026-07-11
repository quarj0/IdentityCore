from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification, VerificationStatus
from apps.verification_subjects.models import VerificationSubject


class AuditEventTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.api_client_obj = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Backend",
            scopes_json=["verifications:create", "verifications:read"],
        )
        self.raw_secret = "client-secret"
        self.api_client_obj.set_client_secret(self.raw_secret)
        self.api_client_obj.save()
        self.policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )

    def api_client_headers(self):
        return {
            "HTTP_X_CLIENT_ID": self.api_client_obj.client_id,
            "HTTP_AUTHORIZATION": f"Bearer {self.raw_secret}",
        }

    def test_login_creates_audit_event(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="user.login",
                target_type="platform_user",
                target_id=self.user.public_id,
            ).exists()
        )

    def test_verification_created_creates_audit_event(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.api_client_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification_id = response.data["data"]["id"]
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="verification.created",
                target_type="verification",
                target_id=verification_id,
            ).exists()
        )

    def test_manual_decision_creates_audit_event(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=VerificationSubject.objects.create(
                tenant=self.tenant,
                full_name="Reviewer Case",
            ),
            purpose="Manual review case",
            expires_at=timezone.now() + timedelta(hours=1),
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("manual-review-decision", kwargs={"verification_id": verification.public_id}),
            {
                "decision": "verified",
                "reason_code": "evidence_confirmed",
                "reason_detail": "Document and selfie match after manual review.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="verification.verified",
                target_type="verification",
                target_id=verification.public_id,
            ).exists()
        )

    def test_audit_event_list_is_tenant_scoped(self):
        AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type="platform_user",
            actor_id=self.user.public_id,
            action="user.login",
            target_type="platform_user",
            target_id=self.user.public_id,
        )
        other_org = Organization.objects.create(name="Beta", slug="beta")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Beta Tenant",
            slug="beta-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        AuditEvent.objects.create(
            tenant=other_tenant,
            actor_type="platform_user",
            actor_id=other_user.public_id,
            action="user.login",
            target_type="platform_user",
            target_id=other_user.public_id,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("audit-event-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["results"]), 1)
