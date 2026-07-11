from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy


class VerificationPolicyAPITests(APITestCase):
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
        self.client.force_authenticate(self.user)

    def create_api_client(self, *, scopes=None, tenant=None, user=None, secret="secret"):
        api_client = APIClient(
            tenant=tenant or self.tenant,
            created_by=user or self.user,
            name="Backend",
            scopes_json=scopes or ["policies:read"],
        )
        api_client.set_client_secret(secret)
        api_client.save()
        return api_client, {
            "HTTP_X_CLIENT_ID": api_client.client_id,
            "HTTP_AUTHORIZATION": f"Bearer {secret}",
        }

    def test_create_policy_creates_draft_version_one(self):
        response = self.client.post(
            reverse("verification-policy-list-create"),
            {
                "name": "Default Verification",
                "required_document_types": ["national_id", "passport"],
                "required_liveness_level": "passive",
                "face_match_threshold": "0.8500",
                "manual_review_threshold": "0.6500",
                "verification_expiry_minutes": 1440,
                "media_retention_days": 30,
                "metadata_retention_days": 365,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        policy = VerificationPolicy.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(policy.version, 1)
        self.assertEqual(policy.status, "draft")
        self.assertEqual(policy.required_document_types, ["national_id", "passport"])

    def test_create_policy_increments_version_for_same_name(self):
        VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )

        response = self.client.post(
            reverse("verification-policy-list-create"),
            {
                "name": "Default Verification",
                "required_document_types": ["passport"],
                "required_liveness_level": "active",
                "face_match_threshold": "0.9000",
                "manual_review_threshold": "0.7000",
                "verification_expiry_minutes": 60,
                "media_retention_days": 10,
                "metadata_retention_days": 100,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["version"], 2)

    def test_list_policies_is_tenant_scoped(self):
        VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
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
        VerificationPolicy.objects.create(
            tenant=other_tenant,
            name="Other Policy",
            version=1,
            status="active",
            required_document_types_json=["passport"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=other_user,
        )

        response = self.client.get(reverse("verification-policy-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Default Verification")

    def test_policy_lifecycle_is_versioned_and_active_is_immutable(self):
        create = self.client.post(
            reverse("verification-policy-list-create"),
            {
                "name": "Identity Check",
                "required_document_types": ["national_id"],
                "required_liveness_level": "passive",
                "face_match_threshold": "0.8500",
                "manual_review_threshold": "0.6500",
                "verification_expiry_minutes": 60,
                "media_retention_days": 30,
                "metadata_retention_days": 365,
            }, format="json",
        )
        policy_id = create.data["data"]["id"]
        activate = self.client.post(
            reverse("verification-policy-activate", kwargs={"policy_id": policy_id})
        )
        self.assertEqual(activate.data["data"]["status"], "active")
        update = self.client.patch(
            reverse("verification-policy-detail", kwargs={"policy_id": policy_id}),
            {"description": "Changed"}, format="json",
        )
        self.assertEqual(update.status_code, status.HTTP_400_BAD_REQUEST)
        clone = self.client.post(
            reverse("verification-policy-clone", kwargs={"policy_id": policy_id})
        )
        self.assertEqual(clone.status_code, status.HTTP_201_CREATED)
        self.assertEqual(clone.data["data"]["version"], 2)
        self.assertEqual(clone.data["data"]["status"], "draft")

    def test_api_client_can_list_only_active_policies_with_read_scope(self):
        self.client.force_authenticate(user=None)
        active = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Active Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )
        VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Draft Verification",
            version=1,
            status="draft",
            required_document_types_json=["passport"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )
        _, headers = self.create_api_client()

        response = self.client.get(reverse("verification-policy-list-create"), **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data["data"]], [active.public_id])

    def test_api_client_policy_detail_requires_active_policy_in_same_tenant(self):
        self.client.force_authenticate(user=None)
        active = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Active Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )
        archived = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Archived Verification",
            version=1,
            status="archived",
            required_document_types_json=["passport"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )
        other_org = Organization.objects.create(name="Gamma", slug="gamma")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Gamma Tenant",
            slug="gamma-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="gamma@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        other_policy = VerificationPolicy.objects.create(
            tenant=other_tenant,
            name="Other Active",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold=Decimal("0.8500"),
            manual_review_threshold=Decimal("0.6500"),
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=other_user,
        )
        _, headers = self.create_api_client()

        active_response = self.client.get(
            reverse("verification-policy-detail", kwargs={"policy_id": active.public_id}),
            **headers,
        )
        archived_response = self.client.get(
            reverse("verification-policy-detail", kwargs={"policy_id": archived.public_id}),
            **headers,
        )
        other_response = self.client.get(
            reverse("verification-policy-detail", kwargs={"policy_id": other_policy.public_id}),
            **headers,
        )

        self.assertEqual(active_response.status_code, status.HTTP_200_OK)
        self.assertEqual(archived_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_client_policy_read_requires_policy_scope(self):
        self.client.force_authenticate(user=None)
        _, headers = self.create_api_client(scopes=["verifications:read"])

        response = self.client.get(reverse("verification-policy-list-create"), **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_client_cannot_create_policy(self):
        self.client.force_authenticate(user=None)
        _, headers = self.create_api_client()

        response = self.client.post(
            reverse("verification-policy-list-create"),
            {
                "name": "SDK Draft",
                "required_document_types": ["national_id"],
                "required_liveness_level": "passive",
                "face_match_threshold": "0.8500",
                "manual_review_threshold": "0.6500",
                "verification_expiry_minutes": 1440,
                "media_retention_days": 30,
                "metadata_retention_days": 365,
            },
            format="json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
