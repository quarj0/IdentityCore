from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.biometrics.models import FaceMatch, LivenessCheck
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification, VerificationStatus


class VerificationWorkflowTests(APITestCase):
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
        self.api_client = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Backend",
            scopes_json=["verifications:create", "verifications:read"],
        )
        self.raw_secret = "client-secret"
        self.api_client.set_client_secret(self.raw_secret)
        self.api_client.save()

    def auth_headers(self):
        return {
            "HTTP_X_CLIENT_ID": self.api_client.client_id,
            "HTTP_AUTHORIZATION": f"Bearer {self.raw_secret}",
        }

    def test_create_verification_creates_subject_and_session(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "verification_subject": {
                    "full_name": "Kwame Mensah",
                    "email": "kwame@example.com",
                    "phone_number": "+233500000000",
                },
                "policy_id": "pol_01JABC",
                "redirect_url": "https://example.com/verification-complete",
                "metadata": {"source": "mobile_app"},
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["id"].startswith("ver_"))
        self.assertTrue(response.data["data"]["session_id"].startswith("ses_"))
        verification = Verification.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(verification.verification_subject.external_reference, "customer_12345")

    def test_list_verifications_is_tenant_scoped(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.auth_headers(),
        )
        verification_id = response.data["data"]["id"]

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
        other_client = APIClient(
            tenant=other_tenant,
            created_by=other_user,
            name="Other Backend",
            scopes_json=["verifications:create", "verifications:read"],
        )
        other_client.set_client_secret("other-secret")
        other_client.save()
        self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "beta_123",
                "purpose": "Another verification",
                "verification_subject": {"full_name": "Ama Asare"},
            },
            format="json",
            HTTP_X_CLIENT_ID=other_client.client_id,
            HTTP_AUTHORIZATION="Bearer other-secret",
        )

        list_response = self.client.get(reverse("verification-list-create"), **self.auth_headers())
        ids = [item["id"] for item in list_response.data["data"]["results"]]
        self.assertEqual(ids, [verification_id])

    def test_detail_requires_read_scope(self):
        self.api_client.scopes_json = ["verifications:create"]
        self.api_client.save(update_fields=["scopes_json", "updated_at"])
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(full_name="Kwame"),
            purpose="Test",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.PENDING_CONSENT,
        )

        response = self.client.get(
            reverse("verification-detail", kwargs={"verification_id": verification.public_id}),
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_verification_marks_cancelled(self):
        create_response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.auth_headers(),
        )
        verification_id = create_response.data["data"]["id"]

        response = self.client.post(
            reverse("verification-cancel", kwargs={"verification_id": verification_id}),
            {"reason": "User abandoned onboarding"},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], VerificationStatus.CANCELLED)

    def test_detail_includes_latest_liveness_and_face_match_states(self):
        subject = self.tenant.verification_subjects.create(full_name="Kwame")
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Test",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.PROCESSING,
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=subject,
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
            captured_at=self.tenant.created_at,
        )
        selfie_capture = self.tenant.selfie_captures.create(
            verification=verification,
            verification_subject=subject,
            storage_key="uploads/selfies/upl_01JSELFIE",
            storage_provider="local",
            capture_type="image",
            mime_type="image/jpeg",
            file_size_bytes=0,
            checksum_sha256="",
            face_count=1,
            status="uploaded",
            captured_at=self.tenant.created_at,
        )
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=selfie_capture,
            liveness_type="passive",
            status="inconclusive",
            checked_at=self.tenant.created_at,
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=selfie_capture,
            identity_document=identity_document,
            document_capture=document_capture,
            status="inconclusive",
            matched_at=self.tenant.created_at,
        )

        response = self.client.get(
            reverse("verification-detail", kwargs={"verification_id": verification.public_id}),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["checks"]["liveness"]["status"], "inconclusive")
        self.assertEqual(response.data["data"]["checks"]["face_match"]["status"], "inconclusive")

    def test_create_verification_copies_policy_snapshot(self):
        policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id", "passport"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=60,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )

        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_999",
                "purpose": "Customer onboarding verification",
                "policy_id": policy.public_id,
                "verification_subject": {
                    "full_name": "Kwame Mensah",
                },
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification = Verification.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(verification.policy_public_id, policy.public_id)
        self.assertEqual(verification.policy_snapshot_json["id"], policy.public_id)
        self.assertEqual(verification.policy_snapshot_json["required_liveness_level"], "passive")
