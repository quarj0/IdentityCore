from apps.access_control.test_helpers import grant_review_permission
from datetime import timedelta
from unittest import skipUnless
from django.db import connection
from django.test import TransactionTestCase

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import PlatformUser
from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.identity_documents.models import IdentityDocument
from apps.verifications import tests as fixtures
from apps.verifications.models import ReviewQueue, ReviewQueueEntry, ReviewQueueMember
from apps.verifications.review_queues import admit_tenant, assign_next
from apps.verifications.serializers import ManualReviewDecisionSerializer


class ReviewQueueTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def queue(self, **kwargs):
        return ReviewQueue.objects.create(
            tenant=self.tenant, environment="sandbox", name="Document Review", **kwargs
        )

    def member(self, queue, user=None, *, with_review_permission=True, **kwargs):
        if with_review_permission:
            grant_review_permission(user or self.tenant_reviewer)
        return ReviewQueueMember.objects.create(
            queue=queue, user=user or self.tenant_reviewer, **kwargs
        )

    def grant_manage(self):
        permission, _ = Permission.objects.get_or_create(
            code="manage_team", defaults={"name": "Manage team"}
        )
        role = Role.objects.create(
            tenant=self.tenant, name="Queue manager", scope="tenant"
        )
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(
            user=self.tenant_reviewer, role=role, tenant=self.tenant
        )

    def test_priority_sla_and_skills_are_frozen_on_admission(self):
        queue = self.queue(priority=10, sla_minutes=15, required_skills=["document"])
        self.member(queue, skills=["document"])
        started = timezone.now() - timedelta(hours=1)
        self.tenant_case.review_queued_at = started
        self.tenant_case.save(update_fields=["review_queued_at"])
        admit_tenant(self.tenant.pk, "sandbox")
        entry = ReviewQueueEntry.objects.get(verification=self.tenant_case)
        self.assertEqual(entry.due_at, started + timedelta(minutes=15))
        queue.priority = 100
        queue.sla_minutes = 100
        queue.required_skills = ["new_skill"]
        queue.save()
        admit_tenant(self.tenant.pk, "sandbox")
        entry.refresh_from_db()
        self.assertEqual(entry.priority, 10)
        self.assertEqual(entry.required_skills, ["document"])
        self.assertFalse(
            ReviewQueueEntry.objects.filter(verification=self.platform_case).exists()
        )

    def test_country_from_classification_not_applicant_metadata(self):
        restricted = self.queue(priority=100, country_codes=["GH"])
        fallback = self.queue(priority=1)
        self.tenant_case.metadata_json = {
            "country_code": "GH",
            "predicted_country_code": "GH",
        }
        self.tenant_case.save()
        admit_tenant(self.tenant.pk, "sandbox")
        self.assertEqual(self.tenant_case.queue_entry.queue, fallback)
        case = self._create_case("Classified Case", metadata={})
        IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=case,
            verification_subject=case.verification_subject,
            document_type_id="passport",
            extracted_data_json={
                "document_classification": {"predicted_country_code": "GH"}
            },
        )
        admit_tenant(self.tenant.pk, "sandbox")
        self.assertEqual(case.queue_entry.queue, restricted)

    def test_least_loaded_and_longest_idle_reviewers_receive_cases(self):
        queue = self.queue()
        first = self.member(queue)
        second_user = PlatformUser.objects.create_user(
            email="other-reviewer@example.com",
            password="SyntheticPassword123!",
            tenant=self.tenant,
            status="active",
        )
        second = self.member(queue, second_user)
        cases = [self.tenant_case] + [
            self._create_case(f"Fair Case {i}", metadata={}) for i in range(3)
        ]
        assigned = [assign_next(queue, actor=self.tenant_reviewer) for _ in cases]
        self.assertEqual(
            [case.assigned_reviewer_id for case in assigned],
            [first.user_id, second.user_id, first.user_id, second.user_id],
        )
        self.assertIsNone(assign_next(queue, actor=self.tenant_reviewer))
        self.assertEqual(len({case.pk for case in assigned}), 4)

    def test_unavailable_unskilled_inactive_and_own_case_are_not_assigned(self):
        queue = self.queue(required_skills=["document"])
        member = self.member(queue, skills=[])
        self.assertIsNone(assign_next(queue, actor=self.tenant_reviewer))
        member.skills = ["document"]
        member.save()
        self.tenant_case.created_by = self.tenant_reviewer
        self.tenant_case.save()
        self.assertIsNone(assign_next(queue, actor=self.tenant_reviewer))
        self.tenant_case.created_by = None
        self.tenant_case.verification_subject.email = self.tenant_reviewer.email
        self.tenant_case.verification_subject.save()
        self.tenant_case.save()
        self.assertIsNone(assign_next(queue, actor=self.tenant_reviewer))
        member.available = False
        member.save()
        with self.assertRaises(ValidationError):
            assign_next(queue, actor=self.tenant_reviewer)

    def test_configured_queue_blocks_direct_claim_and_preserves_assignment(self):
        queue = self.queue()
        self.member(queue)
        serializer = ManualReviewDecisionSerializer(
            data={"decision": "verified", "reason_code": "manual_verified"}
        )
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save(
                verification=self.tenant_case, decided_by=self.tenant_reviewer
            )
        assigned = assign_next(queue, actor=self.tenant_reviewer)
        decision = serializer.save(
            verification=assigned, decided_by=self.tenant_reviewer
        )
        self.assertEqual(decision.decision, "verified")
        self.tenant_case.refresh_from_db()
        self.assertEqual(self.tenant_case.assigned_reviewer_id, self.tenant_reviewer.pk)

    def test_configuration_requires_permission_and_never_crosses_tenant_or_environment(
        self,
    ):
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        data = {
            "name": "Priority",
            "environment": "sandbox",
            "country_codes": ["GH"],
            "required_skills": ["document"],
        }
        url = reverse("review-queue-list")
        self.assertEqual(client.post(url, data, format="json").status_code, 403)
        self.grant_manage()
        response = client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        queue = ReviewQueue.objects.get(public_id=response.data["data"]["queue_id"])
        member_url = reverse(
            "review-queue-members", kwargs={"queue_id": queue.public_id}
        )
        self.assertEqual(
            client.put(
                member_url, {"user_id": self.platform_reviewer.public_id}, format="json"
            ).status_code,
            404,
        )
        self.assertEqual(
            client.put(
                member_url,
                {"user_id": self.tenant_reviewer.public_id, "skills": ["document"]},
                format="json",
            ).status_code,
            200,
        )
        patch_url = reverse("review-queue-detail", kwargs={"queue_id": queue.public_id})
        self.assertEqual(
            client.patch(
                patch_url, {"environment": "production"}, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(
            client.post(
                url, {**data, "country_codes": ["gh"]}, format="json"
            ).status_code,
            400,
        )
        client.force_authenticate(self.platform_reviewer)
        self.assertEqual(client.get(url).status_code, 403)

    def test_fair_recency_is_shared_across_queues_but_not_environments(self):
        first_queue = self.queue(priority=10)
        second_user = PlatformUser.objects.create_user(
            email="cross-queue@example.test",
            password="SyntheticPassword123!",
            tenant=self.tenant,
            status="active",
        )
        self.member(first_queue)
        self.member(first_queue, second_user)
        first_case = assign_next(first_queue, actor=self.tenant_reviewer)
        serializer = ManualReviewDecisionSerializer(
            data={"decision": "verified", "reason_code": "manual_verified"}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(verification=first_case, decided_by=self.tenant_reviewer)
        first_queue.active = False
        first_queue.save()
        second_queue = self.queue()
        self.member(second_queue)
        self.member(second_queue, second_user)
        production_queue = self.queue()
        production_queue.environment = "production"
        production_queue.save()
        production_member = self.member(production_queue)
        self._create_case("Second Queue Case", metadata={})
        case = assign_next(second_queue, actor=self.tenant_reviewer)
        self.assertEqual(case.assigned_reviewer_id, second_user.pk)
        self.assertIsNotNone(first_queue.members.get(user=second_user).last_assigned_at)
        production_member.refresh_from_db()
        self.assertIsNone(production_member.last_assigned_at)

    def test_deleted_subject_is_not_assigned(self):
        queue = self.queue()
        self.member(queue)
        self.tenant_case.verification_subject.soft_delete()
        self.assertIsNone(assign_next(queue, actor=self.tenant_reviewer))
        self.tenant_case.refresh_from_db()
        self.assertIsNone(self.tenant_case.assigned_reviewer_id)

    def test_deleted_manager_role_cannot_configure_queues(self):
        from rest_framework.test import APIClient

        self.grant_manage()
        Role.objects.get(name="Queue manager", tenant=self.tenant).soft_delete()
        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        response = client.post(
            reverse("review-queue-list"),
            {"name": "Denied", "environment": "sandbox"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ReviewQueue.objects.exists())

    def test_overdue_country_and_skill_filters_expose_only_workflow_metadata(self):
        from rest_framework.test import APIClient

        queue = self.queue(required_skills=["document"])
        self.member(queue, skills=["document"])
        admit_tenant(self.tenant.pk, "sandbox")
        entry = self.tenant_case.queue_entry
        entry.country_code = "GH"
        entry.due_at = timezone.now() - timedelta(minutes=1)
        entry.save()
        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        url = reverse("review-queue-cases", kwargs={"queue_id": queue.public_id})
        response = client.get(
            url, {"overdue": "true", "country": "GH", "skill": "document"}
        )
        self.assertEqual(response.status_code, 200, response.data)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["overdue"])
        self.assertNotIn("subject", results[0])
        self.assertEqual(
            client.get(url, {"skill": "different"}).data["data"]["results"], []
        )


class ReviewQueueRaceTests(TransactionTestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    @skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
    def test_simultaneous_assignment_never_assigns_one_case_twice(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections

        queue = ReviewQueue.objects.create(
            tenant=self.tenant, environment="sandbox", name="Concurrent"
        )
        ReviewQueueMember.objects.create(queue=queue, user=self.tenant_reviewer)
        ready = Barrier(2)

        def assign(_):
            close_old_connections()
            try:
                current = ReviewQueue.objects.get(pk=queue.pk)
                actor = PlatformUser.objects.get(pk=self.tenant_reviewer.pk)
                ready.wait(timeout=15)
                result = assign_next(current, actor=actor)
                return result.pk if result else None
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(assign, range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(ReviewQueueEntry.objects.count(), 1)
        self.tenant_case.refresh_from_db()
        self.assertEqual(self.tenant_case.assigned_reviewer_id, self.tenant_reviewer.pk)
