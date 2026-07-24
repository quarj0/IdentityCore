import json
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.test.utils import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.access_control.models import UserRole
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.access_control.models import Role, RoleScope
from apps.analytics.models import AnalyticsDashboard
from apps.billing.models import BillingRecord
from apps.feature_flags.models import FeatureFlag
from apps.incidents.models import Incident
from apps.providers.models import Provider, ProviderStatus, ProviderType
from apps.organizations.models import Organization, OrganizationSupportingDocument
from apps.risk.models import RiskAssessment
from apps.security.models import SecurityCase
from apps.support.models import SupportTicket
from apps.tenants.models import Tenant
from apps.templates.models import Template
from apps.webhooks.models import WebhookEndpoint
from apps.verification_policies.models import VerificationPolicy
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

    def create_supporting_document(self, organization, tenant, user):
        return OrganizationSupportingDocument.objects.create(
            organization=organization,
            tenant=tenant,
            uploaded_by=user,
            filename="certificate.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            storage_key="organizations/documents/certificate.pdf",
            status="uploaded",
        )

    def test_countries_query_returns_full_public_catalog(self):
        response = self.post_graphql(
            """
                query Countries {
                  countries {
                    code
                    name
                  }
                }
            """,
            token="",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        country_map = {
            item["code"]: item["name"] for item in payload["data"]["countries"]
        }
        self.assertEqual(country_map["GH"], "Ghana")
        self.assertIn("NG", country_map)
        self.assertIn("US", country_map)

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

        response = self.post_graphql("""
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
            """)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        self.assertEqual(
            payload["data"]["verifications"][0]["id"], verification.public_id
        )
        self.assertEqual(
            payload["data"]["verifications"][0]["riskAssessment"]["riskLevel"], "high"
        )

    def test_create_administrator_onboarding_verification_is_server_linked(self):
        response = self.post_graphql(
            """
                mutation CreateAdministratorVerification {
                  createAdministratorOnboardingVerification {
                    verificationId
                    sessionId
                    sessionToken
                    verificationUrl
                    action
                  }
                }
            """
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertNotIn("errors", payload)
        launch = payload["data"]["createAdministratorOnboardingVerification"]
        verification = Verification.objects.get(public_id=launch["verificationId"])
        self.assertEqual(
            verification.metadata_json["workflow"], "administrator_onboarding"
        )
        self.assertEqual(verification.created_by, self.user)
        self.assertIn("#token=", launch["verificationUrl"])
        self.assertNotIn("?token=", launch["verificationUrl"])
        self.assertEqual(launch["action"], "initial")

        resumed_response = self.post_graphql(
            """
                mutation ResumeAdministratorVerification {
                  createAdministratorOnboardingVerification {
                    verificationId
                    sessionId
                    action
                  }
                }
            """
        )
        resumed = resumed_response.json()["data"][
            "createAdministratorOnboardingVerification"
        ]
        self.assertEqual(resumed["verificationId"], verification.public_id)
        self.assertEqual(resumed["action"], "resume")
        self.assertNotEqual(resumed["sessionId"], launch["sessionId"])

        verification.status = "verified"
        verification.save(update_fields=["status", "updated_at"])
        blocked = self.post_graphql(
            """
                mutation BlockCasualReverification {
                  createAdministratorOnboardingVerification { action }
                }
            """
        ).json()
        self.assertIn("already verified", blocked["errors"][0]["message"])

        reverification = self.post_graphql(
            """
                mutation ControlledReverification($reason: String!) {
                  createAdministratorOnboardingVerification(reason: $reason) {
                    verificationId
                    action
                  }
                }
            """,
            {"reason": "periodic_compliance_renewal"},
        ).json()["data"]["createAdministratorOnboardingVerification"]
        self.assertEqual(reverification["action"], "reverify")
        self.assertNotEqual(reverification["verificationId"], verification.public_id)

        Verification.objects.filter(public_id=reverification["verificationId"]).update(
            status="verified"
        )
        custom_reverification = self.post_graphql(
            """
                mutation CustomReverification($reason: String!) {
                  createAdministratorOnboardingVerification(reason: $reason) {
                    action
                  }
                }
            """,
            {"reason": "custom:Administrator changed legal name"},
        ).json()["data"]["createAdministratorOnboardingVerification"]
        self.assertEqual(custom_reverification["action"], "reverify")

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
                      organizationCountry
                      organizationTier
                      organizationStatus
                      tenantStatus
                      administratorEmail
                      administratorCountry
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
                    "organizationName": "Sunrise Health",
                    "organizationType": "healthcare_provider",
                    "organizationCountry": "ng",
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
        self.assertEqual(onboarding["organizationCountry"], "NG")
        self.assertEqual(onboarding["administratorCountry"], "NG")
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

    def test_register_organization_onboarding_rejects_public_email_domains(self):
        response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    nextAction
                  }
                }
            """,
            {
                "input": {
                    "fullName": "Ama Mensah",
                    "businessEmail": "ama@gmail.com",
                    "password": "StrongPassword123!",
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
        self.assertIn("errors", payload)
        self.assertIn("organization email address", payload["errors"][0]["message"])

    def test_register_organization_onboarding_rejects_invalid_country_code(self):
        response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    nextAction
                  }
                }
            """,
            {
                "input": {
                    "fullName": "Ama Mensah",
                    "businessEmail": "ama@sunrise.example",
                    "password": "StrongPassword123!",
                    "organizationName": "Sunrise Health",
                    "organizationType": "healthcare_provider",
                    "organizationCountry": "ZZ",
                    "website": "https://sunrise.example",
                    "supportEmail": "support@sunrise.example",
                    "phoneNumber": "+233201234567",
                }
            },
            token="",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("errors", payload)
        self.assertIn("country", payload["errors"][0]["message"].lower())

    def test_register_organization_onboarding_rejects_missing_country(self):
        response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    nextAction
                  }
                }
            """,
            {
                "input": {
                    "fullName": "Ama Mensah",
                    "businessEmail": "ama@sunrise.example",
                    "password": "StrongPassword123!",
                    "organizationName": "Sunrise Health",
                    "organizationType": "healthcare_provider",
                    "organizationCountry": "",
                    "website": "https://sunrise.example",
                    "supportEmail": "support@sunrise.example",
                    "phoneNumber": "+233201234567",
                }
            },
            token="",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("errors", payload)
        self.assertIn("country", payload["errors"][0]["message"].lower())

    def test_register_organization_onboarding_rejects_weak_passwords(self):
        response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    nextAction
                  }
                }
            """,
            {
                "input": {
                    "fullName": "Ama Mensah",
                    "businessEmail": "ama@sunrise.example",
                    "password": "weakpass",
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
        self.assertIn("errors", payload)
        self.assertIn("Password must include", payload["errors"][0]["message"])

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
        self.assertEqual(
            confirm_payload["nextAction"], "submit_organization_verification"
        )
        self.assertEqual(confirm_payload["onboarding"]["administratorStatus"], "active")
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

        repeated_response = self.post_graphql(
            """
                mutation VerifyOnboardingEmailAgain($token: String!) {
                  verifyOrganizationOnboardingEmail(token: $token) {
                    message
                    emailAlreadyVerified
                    nextAction
                  }
                }
            """,
            {"token": token},
            token="",
        )
        repeated_payload = repeated_response.json()["data"][
            "verifyOrganizationOnboardingEmail"
        ]
        self.assertTrue(repeated_payload["emailAlreadyVerified"])
        self.assertEqual(
            repeated_payload["message"],
            "Email already verified. You can continue onboarding.",
        )
        self.assertEqual(
            repeated_payload["nextAction"], "submit_organization_verification"
        )

        onboarding_user = PlatformUser.objects.get(
            public_id=onboarding["administratorUserId"]
        )
        self.assertTrue(UserRole.objects.filter(user=onboarding_user).exists())
        login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": onboarding_user.email, "password": "StrongPassword123!"},
            format="json",
        )
        onboarding_token = login_response.data["data"]["tokens"]["access"]
        self.create_supporting_document(
            onboarding_user.tenant.organization,
            onboarding_user.tenant,
            onboarding_user,
        )

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
            admin_identity_payload["onboarding"]["administratorIdentityVerificationId"],
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
        submitted_at = timezone.now().isoformat()
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
                "email_verification": {
                    "required": True,
                    "verified_at": timezone.now().isoformat(),
                },
                "organization_verification": {
                    "submitted_at": submitted_at,
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

        response = self.post_graphql("""
                query OrganizationOnboarding {
                  organizationOnboarding {
                    organizationId
                    organizationType
                    supportEmail
                    phoneNumber
                    onboardingStatus
                    currentStep
                    organizationVerificationSubmittedAt
                    organizationVerificationEditable
                    organizationVerificationReviewStatus
                    businessRegistrationNumber
                    taxIdentificationNumber
                    registeredAddress
                    officialWebsite
                  }
                }
            """)

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
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["organizationVerificationSubmittedAt"],
            submitted_at,
        )
        self.assertFalse(
            payload["data"]["organizationOnboarding"]["organizationVerificationEditable"]
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"][
                "organizationVerificationReviewStatus"
            ],
            "submitted",
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["businessRegistrationNumber"],
            "BRN-1",
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["taxIdentificationNumber"],
            "",
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["registeredAddress"],
            "Accra",
        )
        self.assertEqual(
            payload["data"]["organizationOnboarding"]["officialWebsite"],
            "https://acme.example",
        )

    @override_settings(DEBUG=True)
    def test_organization_verification_reopens_after_needs_information_review(self):
        registration_response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    onboarding {
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
        token = parse_qs(
            urlparse(onboarding_payload["debugEmailVerificationUrl"]).query
        )["token"][0]

        confirm_response = self.post_graphql(
            """
                mutation VerifyOnboardingEmail($token: String!) {
                  verifyOrganizationOnboardingEmail(token: $token) {
                    onboarding {
                      organizationId
                    }
                  }
                }
            """,
            {"token": token},
            token="",
        )
        organization_id = confirm_response.json()["data"][
            "verifyOrganizationOnboardingEmail"
        ]["onboarding"]["organizationId"]
        onboarding_user = PlatformUser.objects.get(
            public_id=onboarding_payload["onboarding"]["administratorUserId"]
        )
        login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": onboarding_user.email, "password": "StrongPassword123!"},
            format="json",
        )
        onboarding_token = login_response.data["data"]["tokens"]["access"]
        self.create_supporting_document(
            onboarding_user.tenant.organization,
            onboarding_user.tenant,
            onboarding_user,
        )

        submitted_response = self.post_graphql(
            """
                mutation SubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    onboarding {
                      organizationVerificationReviewStatus
                      organizationVerificationEditable
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
        self.assertEqual(
            submitted_response.json()["data"]["submitOrganizationOnboardingVerification"][
                "onboarding"
            ]["currentStep"],
            "administrator_identity_verification",
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
                      currentStep
                      organizationVerificationEditable
                      organizationVerificationReviewStatus
                      organizationStatus
                      tenantStatus
                    }
                  }
                }
            """,
            {
                "organizationId": organization_id,
                "decision": "needs_information",
                "note": "Please provide clearer company registration details.",
            },
            token=self.platform_access_token,
        )
        review_payload = review_response.json()["data"]["reviewOrganizationOnboarding"]
        self.assertEqual(review_payload["nextAction"], "provide_additional_information")
        self.assertEqual(review_payload["onboarding"]["currentStep"], "organization_verification")
        self.assertEqual(review_payload["onboarding"]["organizationVerificationReviewStatus"], "needs_information")
        self.assertTrue(review_payload["onboarding"]["organizationVerificationEditable"])
        self.assertEqual(review_payload["onboarding"]["organizationStatus"], "pending_review")
        self.assertEqual(review_payload["onboarding"]["tenantStatus"], "pending_review")

        resubmit_response = self.post_graphql(
            """
                mutation SubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    nextAction
                    onboarding {
                      currentStep
                      organizationVerificationEditable
                      organizationVerificationReviewStatus
                    }
                  }
                }
            """,
            {
                "input": {
                    "businessRegistrationNumber": "BRN-2026-002",
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
        resubmit_payload = resubmit_response.json()["data"][
            "submitOrganizationOnboardingVerification"
        ]
        self.assertEqual(
            resubmit_payload["nextAction"],
            "submit_administrator_identity_verification",
        )
        self.assertEqual(
            resubmit_payload["onboarding"]["currentStep"],
            "administrator_identity_verification",
        )
        self.assertFalse(
            resubmit_payload["onboarding"]["organizationVerificationEditable"]
        )
        self.assertEqual(
            resubmit_payload["onboarding"]["organizationVerificationReviewStatus"],
            "submitted",
        )

    @override_settings(DEBUG=True)
    def test_organization_verification_edit_after_approval_requeues_workspace(self):
        registration_response = self.post_graphql(
            """
                mutation RegisterOnboarding($input: RegisterOrganizationOnboardingInput!) {
                  registerOrganizationOnboarding(input: $input) {
                    onboarding {
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
        token = parse_qs(
            urlparse(onboarding_payload["debugEmailVerificationUrl"]).query
        )["token"][0]
        confirm_response = self.post_graphql(
            """
                mutation VerifyOnboardingEmail($token: String!) {
                  verifyOrganizationOnboardingEmail(token: $token) {
                    onboarding {
                      organizationId
                    }
                  }
                }
            """,
            {"token": token},
            token="",
        )
        organization_id = confirm_response.json()["data"][
            "verifyOrganizationOnboardingEmail"
        ]["onboarding"]["organizationId"]
        onboarding_user = PlatformUser.objects.get(
            public_id=onboarding_payload["onboarding"]["administratorUserId"]
        )
        login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": onboarding_user.email, "password": "StrongPassword123!"},
            format="json",
        )
        onboarding_token = login_response.data["data"]["tokens"]["access"]
        self.create_supporting_document(
            onboarding_user.tenant.organization,
            onboarding_user.tenant,
            onboarding_user,
        )

        self.post_graphql(
            """
                mutation SubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    onboarding {
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
        self.post_graphql(
            """
                mutation SubmitAdministratorIdentity($verificationId: String!) {
                  submitAdministratorIdentityOnboardingVerification(
                    verificationId: $verificationId
                  ) {
                    onboarding {
                      currentStep
                    }
                  }
                }
            """,
            {"verificationId": "ver_admin_identity_001"},
            token=onboarding_token,
        )
        self.post_graphql(
            """
                mutation ReviewOnboarding($organizationId: String!, $decision: String!, $note: String!) {
                  reviewOrganizationOnboarding(
                    organizationId: $organizationId
                    decision: $decision
                    note: $note
                  ) {
                    onboarding {
                      organizationStatus
                      tenantStatus
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

        edit_response = self.post_graphql(
            """
                mutation SubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    nextAction
                    onboarding {
                      currentStep
                      organizationStatus
                      tenantStatus
                      onboardingStatus
                      organizationVerificationReviewStatus
                    }
                  }
                }
            """,
            {
                "input": {
                    "businessRegistrationNumber": "BRN-2026-003",
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
        edit_payload = edit_response.json()["data"]["submitOrganizationOnboardingVerification"]
        self.assertEqual(edit_payload["nextAction"], "await_platform_review")
        self.assertEqual(edit_payload["onboarding"]["currentStep"], "platform_review")
        self.assertEqual(edit_payload["onboarding"]["organizationStatus"], "pending_review")
        self.assertEqual(edit_payload["onboarding"]["tenantStatus"], "pending_review")
        self.assertEqual(edit_payload["onboarding"]["onboardingStatus"], "platform_review_pending")
        self.assertEqual(
            edit_payload["onboarding"]["organizationVerificationReviewStatus"],
            "changed_after_approval",
        )

        queue_response = self.post_graphql(
            """
                query OrganizationReviewQueue {
                  organizationReviewQueue(page: 1, pageSize: 20) {
                    organizationId
                    organizationName
                    organizationVerificationReviewStatus
                    organizationVerificationChangedAfterApproval
                    organizationVerificationSubmittedAt
                    organizationVerificationReviewNote
                    organizationStatus
                    tenantStatus
                  }
                }
            """,
            token=self.platform_access_token,
        )
        self.assertEqual(queue_response.status_code, status.HTTP_200_OK)
        queue_payload = queue_response.json()["data"]["organizationReviewQueue"]
        self.assertTrue(queue_payload)
        self.assertEqual(queue_payload[0]["organizationId"], organization_id)
        self.assertEqual(
            queue_payload[0]["organizationVerificationReviewStatus"],
            "changed_after_approval",
        )
        self.assertTrue(queue_payload[0]["organizationVerificationChangedAfterApproval"])


class PlatformAdminGraphQLTests(APITestCase):
    graphql_url = "/api/graphql"

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme", slug="acme-platform-graphql"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Platform Tenant",
            slug="acme-platform-tenant",
            status="active",
        )
        self.tenant_user = PlatformUser.objects.create_user(
            email="tenant-admin@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        login_response = self.client.post(
            "/api/v1/auth/login",
            {"email": self.tenant_user.email, "password": "StrongPassword123!"},
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
        self.provider = Provider.objects.create(
            name="Internal OCR",
            code="internal-ocr",
            provider_type=ProviderType.DOCUMENT,
            status=ProviderStatus.ACTIVE,
        )
        self.policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            description="Primary policy",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.tenant_user,
        )
        self.api_client = APIClient(
            tenant=self.tenant,
            created_by=self.tenant_user,
            name="Platform Admin Client",
            scopes_json=["verifications:create"],
        )
        self.api_client.set_client_secret("client-secret")
        self.api_client.save()
        self.webhook_endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            description="Platform admin webhook",
            events_json=["verification.created"],
            created_by=self.tenant_user,
        )
        self.webhook_endpoint.set_secret("webhook-secret")
        self.webhook_endpoint.save()
        self.billing_record = BillingRecord.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            title="Ghana FinTrust Bank",
            subtitle="Enterprise subscription with usage-based verification billing.",
            status="paid",
            monthly_recurring_revenue="$12,840 MRR",
            monthly_check_count=482100,
            current_invoice="Invoice INV-1048",
            plan="Enterprise",
            billing_cycle="Monthly",
            owner_team="Billing Team",
            notes="Verified by finance ops.",
        )
        self.analytics_dashboard = AnalyticsDashboard.objects.create(
            code="verification_volume",
            title="Verification Volume",
            description="Global verification activity across organizations, countries and workflows.",
            status="live",
            primary_metric="482,910 verifications",
            secondary_metric="+18.7%",
            tertiary_metric="30 days",
            time_window="30 days",
            owner_team="Data Platform",
            config_json={"chart": "timeseries"},
        )
        self.incident = Incident.objects.create(
            title="Webhook delivery latency elevated",
            summary="Retries increased for organization webhooks in Africa West.",
            status="open",
            severity="warning",
            owner_team="Support",
            affected_surface="webhooks",
            detected_at=timezone.now() - timedelta(minutes=12),
            metadata_json={"region": "Africa West"},
        )
        self.security_case = SecurityCase.objects.create(
            title="Suspicious admin login",
            summary="Unusual location and impossible travel signal for platform admin account.",
            status="investigating",
            severity="high",
            owner_team="Security Team",
            signal="impossible travel",
            affected_surface="admin access",
            detected_at=timezone.now() - timedelta(minutes=15),
            metadata_json={"ip": "197.251.xxx.xxx"},
        )
        self.support_ticket = SupportTicket.objects.create(
            organization=self.organization,
            title="Webhook verification result missing",
            summary="Ghana FinTrust Bank reports delayed webhook response for completed verification.",
            status="open",
            priority="high",
            owner_team="Support Lead",
            issue_type="webhook",
            requester_email="support@fintrust.example",
            metadata_json={"channel": "platform-admin"},
        )
        self.template = Template.objects.create(
            name="Ghana Card Standard KYC",
            description="Official Ghana Card verification template with document OCR, face match, liveness and manual review fallback.",
            category="government_id",
            status="published",
            version="v1.4.2",
            countries_json=["Ghana"],
            required_checks_json=["Document OCR", "Face match", "Liveness"],
            usage_count=48210,
            cloned_by_organizations=84,
            owner_team="Compliance Team",
            risk_level="Low",
            created_by=self.tenant_user,
        )
        self.feature_flag = FeatureFlag.objects.create(
            key="passive_liveness_beta",
            title="Passive Liveness Beta",
            description="Gradual rollout for passive liveness checks in verification workflows.",
            status="enabled",
            rollout_percent=35,
            audience="Beta",
            owner_team="AI Platform",
            channel="Internal",
            metadata_json={"organizations": 12},
            created_by=self.tenant_user,
        )

    def post_graphql(
        self, query: str, variables: dict | None = None, token="__default__"
    ):
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        headers = {"content_type": "application/json"}
        if token == "__default__":
            headers["HTTP_AUTHORIZATION"] = f"Bearer {self.access_token}"
        elif token:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.client.post(self.graphql_url, data=json.dumps(payload), **headers)

    def create_supporting_document(self, organization, tenant, user):
        return OrganizationSupportingDocument.objects.create(
            organization=organization,
            tenant=tenant,
            uploaded_by=user,
            filename="certificate.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            storage_key="organizations/documents/certificate.pdf",
            status="uploaded",
        )

    def test_platform_admin_graphql_queries_return_live_admin_data(self):
        response = self.post_graphql(
            """
                query PlatformAdminData {
                  platformAdmins {
                    email
                    isPlatformAdmin
                    roles
                  }
                  platformProviders {
                    code
                    status
                  }
                  platformSettings {
                    key
                    primaryValue
                  }
                  platformVerificationPolicies {
                    id
                    name
                  }
                  platformApiClients {
                    publicId
                    clientId
                  }
                  platformWebhookEndpoints {
                    id
                    url
                  }
                }
            """,
            token=self.platform_access_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()["data"]
        self.assertTrue(payload["platformAdmins"])
        self.assertEqual(payload["platformProviders"][0]["code"], "internal-ocr")
        self.assertTrue(
            any(
                setting["key"] == "security.admin_mfa_required"
                for setting in payload["platformSettings"]
            )
        )
        self.assertEqual(payload["platformVerificationPolicies"][0]["id"], self.policy.public_id)
        self.assertEqual(payload["platformApiClients"][0]["publicId"], self.api_client.public_id)
        self.assertEqual(
            payload["platformWebhookEndpoints"][0]["id"], self.webhook_endpoint.public_id
        )

    def test_platform_admin_graphql_queries_return_remaining_live_console_data(self):
        response = self.post_graphql(
            """
                query PlatformAdminExpandedData {
                  platformDashboardSummary {
                    billingRecordsTotal
                    analyticsDashboardsTotal
                    incidentsTotal
                    securityCasesTotal
                    supportTicketsTotal
                    templatesTotal
                    featureFlagsTotal
                  }
                  platformBillingRecords {
                    id
                    title
                    status
                  }
                  platformAnalyticsDashboards {
                    id
                    title
                    status
                  }
                  platformIncidents {
                    id
                    title
                    status
                  }
                  platformSecurityCases {
                    id
                    title
                    status
                  }
                  platformSupportTickets {
                    id
                    title
                    status
                  }
                  platformTemplates {
                    id
                    name
                    status
                  }
                  platformFeatureFlags {
                    id
                    key
                    status
                  }
                }
            """,
            token=self.platform_access_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()["data"]
        self.assertEqual(payload["platformDashboardSummary"]["billingRecordsTotal"], 1)
        self.assertEqual(payload["platformDashboardSummary"]["analyticsDashboardsTotal"], 1)
        self.assertEqual(payload["platformDashboardSummary"]["incidentsTotal"], 1)
        self.assertEqual(payload["platformDashboardSummary"]["securityCasesTotal"], 1)
        self.assertEqual(payload["platformDashboardSummary"]["supportTicketsTotal"], 1)
        self.assertEqual(payload["platformDashboardSummary"]["templatesTotal"], 1)
        self.assertEqual(payload["platformDashboardSummary"]["featureFlagsTotal"], 1)
        self.assertEqual(payload["platformBillingRecords"][0]["id"], self.billing_record.public_id)
        self.assertEqual(
            payload["platformAnalyticsDashboards"][0]["id"],
            self.analytics_dashboard.public_id,
        )
        self.assertEqual(payload["platformIncidents"][0]["id"], self.incident.public_id)
        self.assertEqual(
            payload["platformSecurityCases"][0]["id"], self.security_case.public_id
        )
        self.assertEqual(
            payload["platformSupportTickets"][0]["id"], self.support_ticket.public_id
        )
        self.assertEqual(payload["platformTemplates"][0]["id"], self.template.public_id)
        self.assertEqual(
            payload["platformFeatureFlags"][0]["id"], self.feature_flag.public_id
        )

    def test_platform_admin_invite_accept_deactivate_and_role_assignment(self):
        with override_settings(DEBUG=True):
            invite_response = self.post_graphql(
                """
                    mutation InvitePlatformAdmin($email: String!, $roleName: String!) {
                      invitePlatformAdmin(email: $email, roleName: $roleName) {
                        invitation {
                          id
                          email
                          roleName
                          status
                        }
                        debugAcceptToken
                      }
                    }
                """,
                {"email": "new-admin@example.com", "roleName": "Platform Admin"},
                token=self.platform_access_token,
            )
        self.assertEqual(invite_response.status_code, status.HTTP_200_OK)
        invite_payload = invite_response.json()["data"]["invitePlatformAdmin"]
        self.assertEqual(invite_payload["invitation"]["status"], "pending")
        self.assertTrue(invite_payload["debugAcceptToken"])

        duplicate_invite_response = self.post_graphql(
            """
                mutation InvitePlatformAdmin($email: String!, $roleName: String!) {
                  invitePlatformAdmin(email: $email, roleName: $roleName) {
                    invitation { id }
                  }
                }
            """,
            {"email": "new-admin@example.com", "roleName": "Platform Admin"},
            token=self.platform_access_token,
        )
        self.assertEqual(duplicate_invite_response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "pending invitation already exists",
            duplicate_invite_response.json()["errors"][0]["message"],
        )

        accept_response = self.post_graphql(
            """
                mutation AcceptPlatformAdminInvitation($token: String!, $password: String!) {
                  acceptPlatformAdminInvitation(token: $token, password: $password) {
                    tokens {
                      access
                    }
                    user {
                      email
                      isPlatformAdmin
                      roles
                    }
                  }
                }
            """,
            {
                "token": invite_payload["debugAcceptToken"],
                "password": "StrongPassword123!",
            },
            token="",
        )
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        accepted_user = accept_response.json()["data"]["acceptPlatformAdminInvitation"]["user"]
        self.assertTrue(accepted_user["isPlatformAdmin"])
        self.assertEqual(accepted_user["email"], "new-admin@example.com")

        platform_role = Role.objects.create(
            name="Operations Reviewer",
            description="Can review platform cases.",
            scope=RoleScope.PLATFORM,
            status="active",
        )
        assign_response = self.post_graphql(
            """
                mutation AssignPlatformRole($userId: String!, $roleId: String!) {
                  assignPlatformRole(userId: $userId, roleId: $roleId) {
                    email
                    roles
                  }
                }
            """,
            {
                "userId": PlatformUser.objects.get(email="new-admin@example.com").public_id,
                "roleId": platform_role.public_id,
            },
            token=self.platform_access_token,
        )
        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "Operations Reviewer",
            assign_response.json()["data"]["assignPlatformRole"]["roles"],
        )

        deactivate_response = self.post_graphql(
            """
                mutation DeactivatePlatformAdmin($userId: String!) {
                  deactivatePlatformAdmin(userId: $userId) {
                    email
                    status
                  }
                }
            """,
            {"userId": PlatformUser.objects.get(email="new-admin@example.com").public_id},
            token=self.platform_access_token,
        )
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            deactivate_response.json()["data"]["deactivatePlatformAdmin"]["status"],
            "inactive",
        )

    def test_senior_reviewer_is_required_for_changed_after_approval_cases(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Pending Reviewer",
            email="reviewer@example.com",
        )
        self.create_supporting_document(self.organization, self.tenant, self.tenant_user)
        self.post_graphql(
            """
                mutation SubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    nextAction
                  }
                }
            """,
            {
                "input": {
                    "businessRegistrationNumber": "BRN-1000",
                    "registeredAddress": "1 Admin Street",
                    "officialWebsite": "https://example.com",
                    "taxIdentificationNumber": "TIN-1000",
                    "supportingDocumentKeys": [
                        "organizations/documents/certificate.pdf"
                    ],
                }
            },
            token=self.access_token,
        )
        self.post_graphql(
            """
                mutation ReviewOrganization($organizationId: String!, $decision: String!, $note: String!) {
                  reviewOrganizationOnboarding(
                    organizationId: $organizationId
                    decision: $decision
                    note: $note
                  ) {
                    onboarding { organizationStatus }
                  }
                }
            """,
            {
                "organizationId": self.organization.public_id,
                "decision": "approved",
                "note": "Approved for production.",
            },
            token=self.platform_access_token,
        )
        self.post_graphql(
            """
                mutation ResubmitOrganizationVerification($input: OrganizationVerificationInput!) {
                  submitOrganizationOnboardingVerification(input: $input) {
                    onboarding {
                      organizationVerificationReviewStatus
                    }
                  }
                }
            """,
            {
                "input": {
                    "businessRegistrationNumber": "BRN-1001",
                    "registeredAddress": "1 Admin Street",
                    "officialWebsite": "https://example.com",
                    "taxIdentificationNumber": "TIN-1001",
                    "supportingDocumentKeys": [
                        "organizations/documents/certificate.pdf"
                    ],
                }
            },
            token=self.access_token,
        )

        assign_case = self.post_graphql(
            """
                mutation AssignReviewer($organizationId: String!, $reviewerId: String!) {
                  assignOrganizationReviewReviewer(
                    organizationId: $organizationId
                    reviewerId: $reviewerId
                  ) {
                    onboarding {
                      platformReviewAssignedReviewerId
                      platformReviewAssignedReviewerName
                      platformReviewStatus
                    }
                  }
                }
            """,
            {
                "organizationId": self.organization.public_id,
                "reviewerId": self.platform_admin.public_id,
            },
            token=self.platform_access_token,
        )
        self.assertEqual(assign_case.status_code, status.HTTP_200_OK)

        escalate_case = self.post_graphql(
            """
                mutation EscalateReview($organizationId: String!, $reason: String!) {
                  escalateOrganizationReview(
                    organizationId: $organizationId
                    reason: $reason
                  ) {
                    onboarding {
                      platformReviewEscalated
                      platformReviewEscalationReason
                    }
                  }
                }
            """,
            {
                "organizationId": self.organization.public_id,
                "reason": "Needs senior approval.",
            },
            token=self.platform_access_token,
        )
        self.assertEqual(escalate_case.status_code, status.HTTP_200_OK)

        blocked = self.post_graphql(
            """
                mutation ReviewOrganization($organizationId: String!, $decision: String!, $note: String!) {
                  reviewOrganizationOnboarding(
                    organizationId: $organizationId
                    decision: $decision
                    note: $note
                  ) {
                    nextAction
                  }
                }
            """,
            {
                "organizationId": self.organization.public_id,
                "decision": "approved",
                "note": "Final approval.",
            },
            token=self.platform_access_token,
        )
        self.assertIn("senior reviewer", blocked.json()["errors"][0]["message"].lower())

        senior_role = Role.objects.create(
            name="Senior Reviewer",
            description="Senior reviewer approval role.",
            scope=RoleScope.PLATFORM,
            status="active",
        )
        assign_senior = self.post_graphql(
            """
                mutation AssignPlatformRole($userId: String!, $roleId: String!) {
                  assignPlatformRole(userId: $userId, roleId: $roleId) {
                    roles
                  }
                }
            """,
            {
                "userId": self.platform_admin.public_id,
                "roleId": senior_role.public_id,
            },
            token=self.platform_access_token,
        )
        self.assertEqual(assign_senior.status_code, status.HTTP_200_OK)
        success = self.post_graphql(
            """
                mutation ReviewOrganization($organizationId: String!, $decision: String!, $note: String!) {
                  reviewOrganizationOnboarding(
                    organizationId: $organizationId
                    decision: $decision
                    note: $note
                  ) {
                    nextAction
                    onboarding {
                      organizationStatus
                      platformReviewStatus
                    }
                  }
                }
            """,
            {
                "organizationId": self.organization.public_id,
                "decision": "approved",
                "note": "Final approval.",
            },
            token=self.platform_access_token,
        )
        self.assertEqual(success.status_code, status.HTTP_200_OK)
        self.assertEqual(
            success.json()["data"]["reviewOrganizationOnboarding"]["onboarding"]["organizationStatus"],
            "active",
        )
