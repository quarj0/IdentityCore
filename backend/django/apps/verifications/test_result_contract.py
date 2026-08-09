import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.organizations.models import Organization
from apps.projects.models import Project, ProjectEnvironment
from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderStatus,
    ProviderType,
)
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)


class VerificationResultContractTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Result Organization", slug="result-organization"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Result Tenant",
            slug="result-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="result-owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.project = Project.objects.create(
            tenant=self.tenant,
            name="Production Results",
            slug="production-results",
            environment=ProjectEnvironment.PRODUCTION,
            created_by=self.user,
        )
        self.api_client = APIClient(
            tenant=self.tenant,
            project=self.project,
            created_by=self.user,
            name="Result client",
            scopes_json=["verifications:read"],
        )
        self.api_client.set_client_secret("result-client-secret")
        self.api_client.save()
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Sensitive Applicant Name",
            email="applicant@example.com",
        )
        now = timezone.now()
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            project=self.project,
            organization=self.organization,
            verification_subject=self.subject,
            policy_public_id="pol_public_result",
            policy_snapshot_json={
                "id": "pol_public_result",
                "name": "Production identity policy",
                "version": 7,
                "secret_configuration": "must-not-leak",
            },
            workflow_snapshot_json={
                "id": "wfv_public_result",
                "workflow_id": "wfl_public_result",
                "version": 3,
                "internal_steps": ["must-not-leak"],
            },
            purpose="Result contract test",
            status=VerificationStatus.VERIFIED,
            completed_at=now,
            expires_at=now + timedelta(hours=1),
        )
        provider = Provider.objects.create(
            tenant=self.tenant,
            name="Managed document provider",
            code="managed-document",
            provider_type=ProviderType.DOCUMENT,
            status=ProviderStatus.ACTIVE,
            configuration_json={"token": "raw-secret-value"},
        )
        self.provider_check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.DOCUMENT_QUALITY,
            status=ProviderCheckStatus.COMPLETED,
            provider_reference="internal-provider-reference",
            request_metadata_json={
                "storage_key": "private/document.jpg",
                "document_number": "GHA-SECRET-123",
            },
            response_metadata_json={
                "model_name": "quality-model",
                "model_version": "2026.08",
                "quality_score": 0.97,
                "raw_text": "Sensitive Applicant Name",
            },
            normalized_result_json={
                "contract_version": "1",
                "status": "validated",
                "quality_score": 0.97,
                "issues": ["document_blurry", "Sensitive Applicant Name"],
                "extracted_fields": {"full_name": "Sensitive Applicant Name"},
            },
            error_code="provider_timeout",
            started_at=now - timedelta(seconds=2),
            completed_at=now,
            duration_ms=2000,
        )
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            decision=VerificationStatus.VERIFIED,
            decision_type=VerificationDecisionType.AUTOMATIC,
            reason_code="risk_rules_approved",
            reason_codes_json=[
                "risk_rules_approved",
                "evidence_confirmed",
                "Sensitive Applicant Name",
            ],
            reason_detail="Reviewer note with Sensitive Applicant Name",
            decided_at=now,
        )

    def auth_headers(self):
        return {
            "HTTP_X_CLIENT_ID": self.api_client.client_id,
            "HTTP_AUTHORIZATION": "Bearer result-client-secret",
        }

    def test_result_is_versioned_and_exposes_only_allowlisted_lineage(self):
        response = self.client.get(
            reverse(
                "verification-result",
                kwargs={"verification_id": self.verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data["data"]
        self.assertEqual(result["schema_version"], "1")
        self.assertEqual(result["verification_id"], self.verification.public_id)
        self.assertEqual(result["status"], VerificationStatus.VERIFIED)
        self.assertEqual(
            result["decision"],
            {
                "outcome": VerificationStatus.VERIFIED,
                "type": VerificationDecisionType.AUTOMATIC,
                "reason_codes": ["risk_rules_approved", "evidence_confirmed"],
                "approval_status": "not_required",
                "contract_version": "1",
                "decided_at": self.verification.decision_record.decided_at.isoformat(),
            },
        )
        self.assertEqual(
            result["policy"], {"policy_id": "pol_public_result", "version": 7}
        )
        self.assertEqual(result["workflow"]["version"], 3)
        check = result["check_provenance"][0]
        self.assertEqual(check["check_id"], self.provider_check.public_id)
        self.assertEqual(check["capability"], ProviderCheckType.DOCUMENT_QUALITY)
        self.assertEqual(check["provider"]["code"], "managed-document")
        self.assertEqual(check["capability_contract_version"], "1")
        self.assertEqual(
            check["evidence"],
            {
                "quality_score": 0.97,
                "model": {"name": "quality-model", "version": "2026.08"},
                "issues": ["document_blurry"],
            },
        )
        self.assertEqual(check["status"], "validated")
        self.assertEqual(check["error_code"], "provider_timeout")
        self.assertEqual(check["duration_ms"], 2000)
        self.assertEqual(
            set(result["timestamps"]),
            {"created_at", "updated_at", "completed_at", "expires_at"},
        )

        encoded = json.dumps(result)
        for forbidden in (
            "Sensitive Applicant Name",
            "applicant@example.com",
            "raw-secret-value",
            "private/document.jpg",
            "GHA-SECRET-123",
            "internal-provider-reference",
            "must-not-leak",
            "request_metadata",
            "response_metadata",
            "normalized_result",
            "reason_detail",
            "extracted_fields",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_result_drops_token_shaped_uncontrolled_codes(self):
        self.provider_check.normalized_result_json = {
            "status": "completed",
            "issues": ["GHA-SECRET-123", "s3://bucket/key", "username123"],
        }
        self.provider_check.error_code = "provider_customer_ghana_card_1234"
        self.provider_check.save(
            update_fields=["normalized_result_json", "error_code", "updated_at"]
        )
        decision = self.verification.decision_record
        decision.reason_code = "GHA-SECRET-123"
        decision.reason_codes_json = ["s3://bucket/key", "username123"]
        decision.save(update_fields=["reason_code", "reason_codes_json", "updated_at"])

        response = self.client.get(
            reverse(
                "verification-result",
                kwargs={"verification_id": self.verification.public_id},
            ),
            **self.auth_headers(),
        )

        result = response.data["data"]
        self.assertEqual(result["decision"]["reason_codes"], [])
        self.assertNotIn("issues", result["check_provenance"][0]["evidence"])
        self.assertIsNone(result["check_provenance"][0]["error_code"])

    def test_result_falls_back_to_response_contract_and_maps_risk_score(self):
        self.provider_check.normalized_result_json = {
            "status": "completed",
            "risk_score": 82.5,
        }
        self.provider_check.response_metadata_json = {"contract_version": "1"}
        self.provider_check.save(
            update_fields=[
                "normalized_result_json",
                "response_metadata_json",
                "updated_at",
            ]
        )

        response = self.client.get(
            reverse(
                "verification-result",
                kwargs={"verification_id": self.verification.public_id},
            ),
            **self.auth_headers(),
        )

        check = response.data["data"]["check_provenance"][0]
        self.assertEqual(check["capability_contract_version"], "1")
        self.assertEqual(check["evidence"]["score"], 82.5)

    def test_result_preserves_tenant_and_environment_scope(self):
        sandbox_project = Project.objects.create(
            tenant=self.tenant,
            name="Sandbox Results",
            slug="sandbox-results",
            environment=ProjectEnvironment.SANDBOX,
            created_by=self.user,
        )
        sandbox_result = Verification.objects.create(
            tenant=self.tenant,
            project=sandbox_project,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Sandbox result",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        other_organization = Organization.objects.create(
            name="Other Result Organization", slug="other-result-organization"
        )
        other_tenant = Tenant.objects.create(
            organization=other_organization,
            name="Other Result Tenant",
            slug="other-result-tenant",
            status="active",
        )
        other_result = Verification.objects.create(
            tenant=other_tenant,
            organization=other_organization,
            verification_subject=VerificationSubject.objects.create(
                tenant=other_tenant,
                full_name="Other Subject",
            ),
            purpose="Other tenant result",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        for verification in (sandbox_result, other_result):
            with self.subTest(verification=verification.public_id):
                response = self.client.get(
                    reverse(
                        "verification-result",
                        kwargs={"verification_id": verification.public_id},
                    ),
                    **self.auth_headers(),
                )
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
