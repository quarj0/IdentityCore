import json
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.test.utils import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.access_control.models import UserRole
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.risk.models import RiskAssessment
from apps.tenants.models import Tenant
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationStatus,
)
from apps.verification_subjects.models import VerificationSubject


class GraphQLAPITests(APITestCase):
    graphql_url = "/api/graphql"

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme", slug="acme-graphql"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme GraphQL Tenant",
            slug="acme-graphql-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="graphql@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": self.user.email, "password": "StrongPassword123!"},
            format="json",
        )
        self.access_token = login_response.data["data"]["tokens"]["access"]
        self.platform_admin = PlatformUser.objects.create_superuser(
            email="platform-admin@example.com",
            password="StrongPassword123!",
        )
        platform_login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": self.platform_admin.email, "password": "StrongPassword123!"},
            format="json",
        )
        self.platform_access_token = platform_login_response.data["data"]["tokens"][
            "access"
        ]

    def graphql_headers(self, token="__default__"):
        headers = {"content_type": "application/json"}
        if token == "__default__":
            headers["HTTP_AUTHORIZATION"] = f"Bearer {self.access_token}"
        elif token:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return headers

    def post_graphql(
        self, query: str, variables: dict | None = None, token="__default__"
    ):
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        return self.client.post(
            self.graphql_url,
            data=json.dumps(payload),
            **self.graphql_headers(token),
        )

    def test_verifications_query_returns_tenant_scoped_dashboard_data(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Akosua Owusu",
            email="akosua@example.com",
        )
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Manual review case",
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=verification,
            risk_score="78.00",
            risk_level="high",
            recommendation="manual_review",
        )

        response = self.post_graphql(
            """
                query VerificationList {
                  verifications(status: "manual_review_required") {
                    id
                    status
                    riskAssessment {
                      riskLevel
                      riskScore
                    }
                    verificationSubject {
                      fullName
                    }
                  }
                }
            """
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        self.assertEqual(
            payload["data"]["verifications"][0]["id"], verification.public_id
        )
        self.assertEqual(
            payload["data"]["verifications"][0]["riskAssessment"]["riskLevel"], "high"
        )

    def test_record_manual_decision_mutation_updates_verification(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Manual Review Subject",
        )
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Manual review case",
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.post_graphql(
            """
                mutation ManualDecision($verificationId: String!, $decision: String!, $reasonCode: String!) {
                  recordManualDecision(
                    verificationId: $verificationId
                    decision: $decision
                    reasonCode: $reasonCode
                  ) {
                    verificationId
                    decision
                    decisionType
                  }
                }
            """,
            {
                "verificationId": verification.public_id,
                "decision": "verified",
                "reasonCode": "evidence_confirmed",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.VERIFIED)
        self.assertTrue(
            VerificationDecision.objects.filter(verification=verification).exists()
        )
        self.assertEqual(
            payload["data"]["recordManualDecision"]["verificationId"],
            verification.public_id,
        )

    @override_settings(DEBUG=True)
    def test_register_organization_onboarding_creates_pending_trial_workspace(self):
        response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    nextAction
                    debugEmailVerificationUrl
                    onboarding {
                      organizationId
                      organizationName
                      organizationType
                      organizationTier
                      organizationStatus
                      tenantStatus
                      administratorEmail
                      administratorStatus
                      requiresEmailVerification
                      onboardingStatus
                      currentStep
                    }
                  }
                }
            """,
            {
                "input": {
                    "fullName": "Ama Mensah",
                    "businessEmail": "ama@sunrise.example",
                    "password": "StrongPassword123!",
                    "country": "GH",
                    "organizationName": "Sunrise Health",
                    "organizationType": "healthcare_provider",
                    "organizationCountry": "GH",
                    "website": "https://sunrise.example",
                    "supportEmail": "support@sunrise.example",
                    "phoneNumber": "+233201234567",
                }
            },
            token="",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        onboarding = payload["data"]["registerOrganizationOnboarding"]["onboarding"]
        debug_url = payload["data"]["registerOrganizationOnboarding"][
            "debugEmailVerificationUrl"
        ]
        self.assertEqual(
            payload["data"]["registerOrganizationOnboarding"]["nextAction"],
            "verify_email",
        )
        self.assertTrue(debug_url)
        self.assertEqual(onboarding["organizationName"], "Sunrise Health")
        self.assertEqual(onboarding["organizationType"], "healthcare_provider")
        self.assertEqual(onboarding["organizationTier"], "trial")
        self.assertEqual(onboarding["administratorStatus"], "inactive")
        self.assertTrue(onboarding["requiresEmailVerification"])
        self.assertEqual(onboarding["onboardingStatus"], "email_verification_pending")
        self.assertEqual(onboarding["currentStep"], "email_verification")
        self.assertEqual(onboarding["organizationStatus"], "pending_email_verification")
        self.assertEqual(onboarding["tenantStatus"], "pending")
        self.assertTrue(
            PlatformUser.objects.filter(email="ama@sunrise.example").exists()
        )
        self.assertFalse(
            UserRole.objects.filter(user__email="ama@sunrise.example").exists()
        )

    @override_settings(DEBUG=True)
    def test_onboarding_mutations_advance_state_after_email_confirmation(self):
        registration_response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    onboarding {
                      organizationId
                      administratorUserId
                    }
                    debugEmailVerificationUrl
                  }
                }
            """,
            {
                "input": {
                    "fullName": "Kojo Addae",
                    "businessEmail": "kojo@atlas.example",
                    "password": "StrongPassword123!",
                    "country": "GH",
                    "organizationName": "Atlas Verify",
                    "organizationType": "startup",
                    "organizationCountry": "GH",
                    "website": "https://atlas.example",
                    "supportEmail": "support@atlas.example",
                    "phoneNumber": "+233244000111",
                }
            },
            token="",
        )
        onboarding_payload = registration_response.json()["data"][
            "registerOrganizationOnboarding"
        ]
        onboarding = onboarding_payload["onboarding"]
        verification_url = onboarding_payload["debugEmailVerificationUrl"]
        token = parse_qs(urlparse(verification_url).query)["token"][0]
        organization_id = onboarding["organizationId"]

        confirm_response = self.post_graphql(
            """
                mutation VerifyOnboardingEmail($token: String!) {
                  verifyOrganizationOnboardingEmail(token: $token) {
                    nextAction
                    onboarding {
                      administratorStatus
                      organizationStatus
                      tenantStatus
                      onboardingStatus
                      currentStep
                    }
                  }
                }
            """,
            {"token": token},
            token="",
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        confirm_payload = confirm_response.json()["data"][
            "verifyOrganizationOnboardingEmail"
        ]
        self.assertEqual(confirm_payload["nextAction"], "submit_organization_verification")
        self.assertEqual(
            confirm_payload["onboarding"]["administratorStatus"], "active"
        )
        self.assertEqual(
            confirm_payload["onboarding"]["onboardingStatus"],
            "organization_verification_required",
        )
        self.assertEqual(
            confirm_payload["onboarding"]["currentStep"],
            "organization_verification",
        )
        self.assertEqual(
            confirm_payload["onboarding"]["organizationStatus"],
            "pending_review",
        )
        self.assertEqual(
            confirm_payload["onboarding"]["tenantStatus"],
            "pending_review",
        )

        onboarding_user = PlatformUser.objects.get(public_id=onboarding["administratorUserId"])
        self.assertTrue(UserRole.objects.filter(user=onboarding_user).exists())
        login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": onboarding_user.email, "password": "StrongPassword123!"},
            format="json",
        )
        onboarding_token = login_response.data["data"]["tokens"]["access"]

        organization_verification_response = self.post_graphql(
            """
                mutation SubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    nextAction
                    onboarding {
                      organizationVerificationSubmittedAt
                      onboardingStatus
                      currentStep
                    }
                  }
                }
            """,
            {
                "input": {
                    "businessRegistrationNumber": "BRN-2026-001",
                    "registeredAddress": "10 Liberation Road, Accra",
                    "officialWebsite": "https://atlas.example",
                    "taxIdentificationNumber": "TIN-8899",
                    "supportingDocumentKeys": [
                        "organizations/documents/certificate.pdf"
                    ],
                }
            },
            token=onboarding_token,
        )
        org_ver_payload = organization_verification_response.json()["data"][
            "submitOrganizationOnboardingVerification"
        ]
        self.assertEqual(
            org_ver_payload["nextAction"],
            "submit_administrator_identity_verification",
        )
        self.assertEqual(
            org_ver_payload["onboarding"]["onboardingStatus"],
            "administrator_identity_verification_required",
        )
        self.assertEqual(
            org_ver_payload["onboarding"]["currentStep"],
            "administrator_identity_verification",
        )
        self.assertTrue(
            org_ver_payload["onboarding"]["organizationVerificationSubmittedAt"]
        )

        admin_identity_response = self.post_graphql(
            """
                mutation SubmitAdministratorIdentity($verificationId: String!) {
                  submitAdministratorIdentityOnboardingVerification(
                    verificationId: $verificationId
                  ) {
                    nextAction
                    onboarding {
                      administratorIdentityVerificationStatus
                      administratorIdentityVerificationId
                      onboardingStatus
                      currentStep
                    }
                  }
                }
            """,
            {"verificationId": "ver_admin_identity_001"},
            token=onboarding_token,
        )
        admin_identity_payload = admin_identity_response.json()["data"][
            "submitAdministratorIdentityOnboardingVerification"
        ]
        self.assertEqual(admin_identity_payload["nextAction"], "await_platform_review")
        self.assertEqual(
            admin_identity_payload["onboarding"][
                "administratorIdentityVerificationStatus"
            ],
            "submitted",
        )
        self.assertEqual(
            admin_identity_payload["onboarding"][
                "administratorIdentityVerificationId"
            ],
            "ver_admin_identity_001",
        )
        self.assertEqual(
            admin_identity_payload["onboarding"]["onboardingStatus"],
            "platform_review_pending",
        )
        self.assertEqual(
            admin_identity_payload["onboarding"]["currentStep"], "platform_review"
        )

        review_response = self.post_graphql(
            """
                mutation ReviewOnboarding($organizationId: String!, $decision: String!, $note: String!) {
                  reviewOrganizationOnboarding(
                    organizationId: $organizationId
                    decision: $decision
                    note: $note
                  ) {
                    nextAction
                    onboarding {
                      organizationStatus
                      tenantStatus
                      organizationTier
                      onboardingStatus
                    }
                  }
                }
            """,
            {
                "organizationId": organization_id,
                "decision": "approved",
                "note": "Onboarding approved for production.",
            },
            token=self.platform_access_token,
        )
        self.assertEqual(review_response.status_code, status.HTTP_200_OK)
        review_payload = review_response.json()["data"]["reviewOrganizationOnboarding"]
        self.assertEqual(review_payload["nextAction"], "organization_active")
        self.assertEqual(review_payload["onboarding"]["organizationStatus"], "active")
        self.assertEqual(review_payload["onboarding"]["tenantStatus"], "active")
        self.assertEqual(review_payload["onboarding"]["organizationTier"], "verified")
        self.assertEqual(review_payload["onboarding"]["onboardingStatus"], "active")

    def test_organization_onboarding_query_returns_authenticated_tenant_state(self):
        self.organization.settings_json = {
            "onboarding": {
                "tier": "trial",
                "status": "organization_verification_required",
                "current_step": "organization_verification",
                "registration": {
                    "organization_type": "enterprise",
                    "organization_country": "GH",
                    "website": "https://acme.example",
                    "support_email": "support@acme.example",
                    "phone_number": "+233200000000",
                },
                "primary_administrator": {
                    "user_id": self.user.public_id,
                    "full_name": "Graph QL",
                    "business_email": self.user.email,
                    "country": "GH",
                },
                "email_verification": {"required": True, "verified_at": timezone.now().isoformat()},
                "organization_verification": {
                    "submitted_at": timezone.now().isoformat(),
                    "business_registration_number": "BRN-1",
                    "tax_identification_number": "",
                    "registered_address": "Accra",
                    "official_website": "https://acme.example",
                    "supporting_document_keys": [],
                },
                "administrator_identity_verification": {
                    "status": "pending",
                    "verification_id": "",
                    "submitted_at": None,
                },
                "platform_review": {
                    "status": "not_started",
                    "reviewed_at": None,
                    "reviewed_by": "",
                    "note": "",
                },
            }
        }
        self.organization.save(update_fields=["settings_json", "updated_at"])

        response = self.post_graphql(
            """
                query OrganizationOnboarding {
                  organizationOnboarding {
                    organizationId
                    organizationType
                    supportEmail
                    phoneNumber
                    onboardingStatus
                    currentStep
                  }
                }
            """
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["organizationId"],
            self.organization.public_id,
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["organizationType"],
            "enterprise",
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["onboardingStatus"],
            "organization_verification_required",
        )
