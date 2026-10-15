from unittest.mock import patch

from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.projects.models import Project
from apps.verifications import tests as fixtures
from apps.verifications.models import VerificationDecision, VerificationApprovalStatus
from config.graphql_schema import schema


class HistoricalReviewProtocolTests(APITestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def graphql(self, query, variables=None):
        request = RequestFactory().post("/api/graphql")
        request.user = self.tenant_reviewer
        return schema.execute_sync(
            query, variable_values=variables, context_value={"request": request}
        )

    def test_pending_graphql_proposal_emits_no_final_outcome(self):
        case = self.tenant_case
        case.policy_snapshot_json = {"maker_checker_required": True}
        case.save(update_fields=["policy_snapshot_json", "updated_at"])
        with patch(
            "config.graphql_mutations.queue_webhook_events", return_value=[]
        ) as webhooks, patch(
            "config.graphql_mutations.queue_verification_status_notifications"
        ) as notifications:
            result = self.graphql(
                'mutation($id:String!){recordManualDecision(verificationId:$id,decision:"verified",reasonCode:"evidence_confirmed"){verificationId decision approvalStatus approvalRequired}}',
                {"id": case.public_id},
            )
        self.assertIsNone(result.errors, result.errors)
        self.assertEqual(
            result.data["recordManualDecision"]["approvalStatus"], "pending"
        )
        self.assertTrue(result.data["recordManualDecision"]["approvalRequired"])
        case.refresh_from_db()
        self.assertEqual(case.status, "manual_review_required")
        self.assertEqual(
            VerificationDecision.objects.get(verification=case).approval_status,
            VerificationApprovalStatus.PENDING,
        )
        webhooks.assert_not_called()
        notifications.assert_not_called()
        self.assertFalse(
            AuditEvent.objects.filter(
                action="verification.verified", target_id=case.public_id
            ).exists()
        )

    def test_rest_webhook_matches_the_committed_manual_outcome(self):
        self.client.force_authenticate(self.tenant_reviewer)
        with patch(
            "apps.verifications.views.queue_webhook_events", return_value=[]
        ) as webhooks, patch(
            "apps.verifications.views.queue_verification_status_notifications"
        ):
            response = self.client.post(
                reverse(
                    "manual-review-decision",
                    kwargs={"verification_id": self.tenant_case.public_id},
                ),
                {"decision": "verified", "reason_code": "evidence_confirmed"},
                format="json",
                HTTP_IDEMPOTENCY_KEY="historical-rest-review",
            )
        self.assertEqual(response.status_code, 200, response.data)
        self.tenant_case.refresh_from_db()
        self.assertEqual(self.tenant_case.status, "verified")
        self.assertEqual(webhooks.call_args.kwargs["payload"]["status"], "verified")

    def test_final_graphql_decision_reports_committed_status(self):
        with patch(
            "config.graphql_mutations.queue_webhook_events", return_value=[]
        ) as webhooks, patch(
            "config.graphql_mutations.queue_verification_status_notifications"
        ):
            result = self.graphql(
                'mutation($id:String!){recordManualDecision(verificationId:$id,decision:"verified",reasonCode:"evidence_confirmed"){approvalStatus approvalRequired}}',
                {"id": self.tenant_case.public_id},
            )
        self.assertIsNone(result.errors, result.errors)
        self.assertEqual(
            result.data["recordManualDecision"],
            {"approvalStatus": "not_required", "approvalRequired": False},
        )
        self.assertEqual(webhooks.call_args.kwargs["payload"]["status"], "verified")
        self.assertTrue(
            AuditEvent.objects.filter(
                action="verification.review_assigned",
                target_id=self.tenant_case.public_id,
            ).exists()
        )

    def test_graphql_rejects_unbounded_or_zero_page_sizes(self):
        for size in [0, 101]:
            with self.subTest(size=size):
                result = self.graphql("{verifications(pageSize:" + str(size) + "){id}}")
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(
                    result.errors[0].message, "pageSize must be between 1 and 100."
                )

    def test_automatic_and_system_review_routing_can_be_resolved_once(self):
        from django.utils import timezone
        from rest_framework.exceptions import ValidationError
        from apps.verifications.serializers import ManualReviewDecisionSerializer

        for decision_type in ["automatic", "system"]:
            with self.subTest(decision_type=decision_type):
                case = self._create_case(decision_type, metadata={})
                original = VerificationDecision.objects.create(
                    tenant=self.tenant,
                    verification=case,
                    decision="manual_review_required",
                    decision_type=decision_type,
                    reason_code="provider_review",
                    decided_at=timezone.now(),
                )
                serializer = ManualReviewDecisionSerializer(
                    data={"decision": "verified", "reason_code": "evidence_confirmed"}
                )
                serializer.is_valid(raise_exception=True)
                decision = serializer.save(
                    verification=case, decided_by=self.tenant_reviewer
                )
                self.assertEqual(decision.pk, original.pk)
                self.assertEqual(case.status, "verified")
                self.assertEqual(
                    decision.evidence_summary_json["automatic_review"]["reason_code"],
                    "provider_review",
                )
                saved_at = decision.decided_at
                repeated = ManualReviewDecisionSerializer(
                    data={"decision": "rejected", "reason_code": "changed_reason"}
                )
                repeated.is_valid(raise_exception=True)
                with self.assertRaises(ValidationError):
                    repeated.save(verification=case, decided_by=self.tenant_reviewer)
                decision.refresh_from_db()
                self.assertEqual(decision.decision, "verified")
                self.assertEqual(decision.decided_at, saved_at)
                self.assertEqual(decision.reason_code, "evidence_confirmed")

    def test_graphql_document_and_decision_fields_match_saved_evidence(self):
        from django.utils import timezone
        from apps.identity_documents.models import IdentityDocument

        case = self.tenant_case
        IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=case,
            verification_subject=case.verification_subject,
            document_type_id="passport",
            status="processed",
        )
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=case,
            decision="manual_review_required",
            decision_type="automatic",
            decided_at=timezone.now(),
            contract_version="1",
            reason_codes_json=["provider_review"],
        )
        result = self.graphql(
            "{verifications{ id checks{document{status}} decision{contractVersion reasonCodes}}}"
        )
        self.assertIsNone(result.errors, result.errors)
        row = next(
            row for row in result.data["verifications"] if row["id"] == case.public_id
        )
        self.assertEqual(row["checks"]["document"]["status"], "processed")
        self.assertEqual(
            row["decision"],
            {"contractVersion": "1", "reasonCodes": ["provider_review"]},
        )

    def test_graphql_clamps_legacy_out_of_range_pages(self):
        for page in [0, 999]:
            with self.subTest(page=page):
                result = self.graphql(
                    "{verifications(page:" + str(page) + ",pageSize:1){id}}"
                )
                self.assertIsNone(result.errors, result.errors)
                self.assertEqual(len(result.data["verifications"]), 1)


class HistoricalCreationProtocolTests(APITestCase):
    setUp = fixtures.VerificationWorkflowTests.setUp
    auth_headers = fixtures.VerificationWorkflowTests.auth_headers

    def create(self, **overrides):
        payload = {
            "purpose": "Historical protocol regression",
            "policy_id": self.policy.public_id,
            "verification_subject": {"full_name": "Synthetic Subject"},
        }
        payload.update(overrides)
        return self.client.post(
            reverse("verification-list-create"),
            payload,
            format="json",
            **self.auth_headers()
        )

    def test_api_metadata_cannot_request_platform_ownership(self):
        response = self.create(metadata={"workflow": "administrator_onboarding"})
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.tenant.verifications.exists())

    def test_denied_environment_audit_survives_validation_rollback(self):
        project = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=self.user,
        )
        self.policy.project = project
        self.policy.save(update_fields=["project", "updated_at"])
        response = self.create()
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.tenant.verifications.exists())
        self.assertEqual(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="environment_scope.denied",
                target_id=self.policy.public_id,
            ).count(),
            1,
        )
