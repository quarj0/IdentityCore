from importlib import import_module
from django.apps import apps
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import PlatformUser
from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.access_control.test_helpers import grant_review_permission
from apps.audit.models import AuditEvent
from apps.verifications import tests as fixtures
from apps.verifications.models import (
    VerificationDecision,
    ReviewQueue,
    ReviewQueueMember,
)
from apps.verifications.serializers import ManualReviewDecisionSerializer
from common.authorization import AuthorizationAction, decide_user_access
from config.graphql_schema import schema


class ReviewerPermissionTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def member(self):
        return PlatformUser.objects.create_user(
            email="unprivileged@example.test",
            password="StrongPassword123!",
            tenant=self.tenant,
            status="active",
        )

    def test_membership_alone_cannot_list_decide_or_inspect_review_evidence(self):
        user = self.member()
        client = APIClient()
        client.force_authenticate(user)
        before = AuditEvent.objects.count()
        paths = [
            ("get", reverse("manual-review-list")),
            (
                "post",
                reverse("manual-review-decision", args=[self.tenant_case.public_id]),
            ),
            (
                "post",
                reverse("manual-review-approval", args=[self.tenant_case.public_id]),
            ),
            (
                "get",
                f"/api/v1/verifications/manual-reviews/{self.tenant_case.public_id}/authenticity",
            ),
        ]
        for method, path in paths:
            response = getattr(client, method)(
                path, {"decision": "verified", "reason_code": "review"}, format="json"
            )
            self.assertIn(response.status_code, {403, 404}, path)
        self.assertEqual(AuditEvent.objects.count(), before)
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.tenant_case).exists()
        )

    def test_graphql_member_cannot_read_queue_or_record_a_decision(self):
        request = RequestFactory().post("/api/graphql")
        request.user = self.member()
        result = schema.execute_sync(
            "{manualReviews{verificationId}}", context_value={"request": request}
        )
        self.assertIsNone(result.errors, result.errors)
        self.assertEqual(result.data["manualReviews"], [])
        result = schema.execute_sync(
            'mutation($id:String!){recordManualDecision(verificationId:$id,decision:"verified",reasonCode:"review"){verificationId}}',
            variable_values={"id": self.tenant_case.public_id},
            context_value={"request": request},
        )
        self.assertTrue(result.errors)
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.tenant_case).exists()
        )

    def test_role_permission_is_required_and_rechecked_at_finalization(self):
        user = self.member()
        role = grant_review_permission(user)
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get(reverse("manual-review-list")).status_code, 200)
        serializer = ManualReviewDecisionSerializer(
            data={"decision": "verified", "reason_code": "review"}
        )
        serializer.is_valid(raise_exception=True)
        RolePermission.objects.filter(
            role=role, permission__code="review_verification"
        ).delete()
        with self.assertRaises(ValidationError):
            serializer.save(verification=self.tenant_case, decided_by=user)
        self.assertEqual(client.get(reverse("manual-review-list")).status_code, 403)
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.tenant_case).exists()
        )

    def test_inactive_deleted_and_unassigned_roles_cannot_authorize_review(self):
        user = self.member()
        role = grant_review_permission(user)
        for field, value in (("status", "inactive"), ("deleted_at", timezone.now())):
            Role.objects.filter(pk=role.pk).update(**{field: value})
            self.assertFalse(
                decide_user_access(
                    user, action=AuthorizationAction.MANUAL_REVIEW
                ).allowed
            )
            Role.objects.filter(pk=role.pk).update(status="active", deleted_at=None)
        UserRole.objects.filter(user=user).delete()
        self.assertFalse(
            decide_user_access(user, action=AuthorizationAction.MANUAL_REVIEW).allowed
        )

    def test_migration_grants_only_designated_system_roles_and_is_idempotent(self):
        system = Role.objects.create(
            tenant=self.tenant,
            name="Tenant Administrator",
            scope="tenant",
            is_system_role=True,
        )
        custom = Role.objects.create(
            tenant=self.tenant,
            name="Verification Officer",
            scope="tenant",
            is_system_role=False,
        )
        grant = import_module(
            "apps.access_control.migrations.0007_review_verification_permission"
        ).grant
        grant(apps, None)
        grant(apps, None)
        self.assertEqual(
            RolePermission.objects.filter(
                role=system, permission__code="review_verification"
            ).count(),
            1,
        )
        self.assertFalse(
            RolePermission.objects.filter(
                role=custom, permission__code="review_verification"
            ).exists()
        )

    def test_queue_membership_does_not_substitute_for_reviewer_permission(self):
        from apps.verifications.review_queues import admit_tenant, assign_next

        user = self.member()
        queue = ReviewQueue.objects.create(
            tenant=self.tenant, name="Synthetic queue", environment="sandbox"
        )
        ReviewQueueMember.objects.create(queue=queue, user=user, available=True)
        admit_tenant(self.tenant.pk, "sandbox")
        with self.assertRaises(ValidationError):
            assign_next(queue, actor=user)
        self.tenant_case.refresh_from_db()
        self.assertIsNone(self.tenant_case.assigned_reviewer_id)
