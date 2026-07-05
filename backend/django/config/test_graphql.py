import json
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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

    def graphql_headers(self):
        return {
            "content_type": "application/json",
            "HTTP_AUTHORIZATION": f"Bearer {self.access_token}",
        }

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

        response = self.client.post(
            self.graphql_url,
            data=json.dumps(
                {
                    "query": """
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
                }
            ),
            **self.graphql_headers(),
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

        response = self.client.post(
            self.graphql_url,
            data=json.dumps(
                {
                    "query": """
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
                    "variables": {
                        "verificationId": verification.public_id,
                        "decision": "verified",
                        "reasonCode": "evidence_confirmed",
                    },
                }
            ),
            **self.graphql_headers(),
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
