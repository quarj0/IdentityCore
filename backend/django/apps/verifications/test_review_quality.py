from copy import deepcopy
from unittest import skipUnless
from django.db import connection
from django.test import TransactionTestCase

from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import PlatformUser
from apps.verifications.models import ReviewQualityAssignment
from apps.verifications.review_quality import complete_sample, sample_final_decision
from apps.verifications.serializers import ManualReviewDecisionSerializer
from apps.verifications import test_review_queues as queue_fixtures
from apps.verifications.test_review_reasons import RULES


class ReviewQualityTests(TestCase):
    setUp = queue_fixtures.ReviewQueueTests.setUp
    _create_case = queue_fixtures.ReviewQueueTests._create_case
    queue = queue_fixtures.ReviewQueueTests.queue
    member = queue_fixtures.ReviewQueueTests.member
    grant_manage = queue_fixtures.ReviewQueueTests.grant_manage

    def configure(self, percent=100, *, checker=False):
        queue = self.queue(sampling_percent=percent)
        self.member(queue)
        self.second = PlatformUser.objects.create_user(
            email="qa-reviewer@example.test",
            password="SyntheticPassword123!",
            tenant=self.tenant,
            status="active",
        )
        self.member(queue, self.second)
        self.tenant_case.policy_snapshot_json = {
            "review_reason_rules": deepcopy(RULES),
            "maker_checker_required": checker,
        }
        self.tenant_case.save()
        from apps.verifications.review_queues import assign_next

        case = assign_next(queue, actor=self.tenant_reviewer)
        self.assertEqual(case.assigned_reviewer_id, self.tenant_reviewer.pk)
        serializer = ManualReviewDecisionSerializer(
            data={"decision": "verified", "reason_code": "evidence_confirmed"}
        )
        serializer.is_valid(raise_exception=True)
        decision = serializer.save(verification=case, decided_by=self.tenant_reviewer)
        self.tenant_case.refresh_from_db()
        return queue, decision

    def test_full_sampling_creates_one_independent_assignment_and_freezes_outcome(self):
        queue, decision = self.configure()
        sample = ReviewQualityAssignment.objects.get()
        self.assertEqual(sample.reviewer_id, self.second.pk)
        self.assertEqual(sample.original_outcome, "verified")
        self.assertEqual(sample.sampling_percent, 100)
        again = sample_final_decision(self.tenant_case, decision)
        self.assertEqual(again.pk, sample.pk)
        self.assertEqual(ReviewQualityAssignment.objects.count(), 1)
        queue.sampling_percent = 0
        queue.save()
        sample.refresh_from_db()
        self.assertEqual(sample.sampling_percent, 100)

    def test_zero_sampling_and_automatic_outcomes_are_not_sampled(self):
        _, decision = self.configure(percent=0)
        self.assertFalse(ReviewQualityAssignment.objects.exists())
        decision.decision_type = "automatic"
        self.assertIsNone(sample_final_decision(self.tenant_case, decision))

    def test_disagreement_is_private_and_does_not_change_final_result(self):
        self.configure()
        sample = ReviewQualityAssignment.objects.get()
        with self.assertRaises(NotFound):
            complete_sample(
                sample,
                actor=self.tenant_reviewer,
                outcome="rejected",
                reason_code="evidence_mismatch",
                notes="Independent assessment",
            )
        sample = complete_sample(
            sample,
            actor=self.second,
            outcome="rejected",
            reason_code="evidence_mismatch",
            notes="Independent assessment",
        )
        self.assertEqual(sample.notes_json, {"notes": "Independent assessment"})
        self.tenant_case.refresh_from_db()
        self.assertEqual(self.tenant_case.status, "verified")
        self.assertEqual(self.tenant_case.decision_record.decision, "verified")
        complete_sample(
            sample,
            actor=self.second,
            outcome="rejected",
            reason_code="evidence_mismatch",
            notes="Independent assessment",
        )
        with self.assertRaises(ValidationError):
            complete_sample(
                sample,
                actor=self.second,
                outcome="verified",
                reason_code="evidence_confirmed",
                notes="",
            )

    def test_original_reviewer_cannot_inspect_list_or_report_their_sample_even_as_manager(
        self,
    ):
        self.configure()
        self.grant_manage()
        sample = ReviewQualityAssignment.objects.get()
        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        self.assertEqual(
            client.get(reverse("review-quality-list")).data["data"]["results"], []
        )
        url = reverse("review-quality-detail", kwargs={"sample_id": sample.public_id})
        self.assertEqual(client.get(url).status_code, 404)
        self.assertEqual(
            client.get(reverse("review-quality-report")).data["data"]["sampled"], 0
        )
        client.force_authenticate(self.second)
        response = client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        fields = response.data["data"]
        for forbidden in (
            "notes",
            "captures",
            "biometrics",
            "document_images",
            "evidence_report",
            "subject",
        ):
            self.assertNotIn(forbidden, fields)
        self.assertEqual(
            client.get(url, {"environment": "production"}).status_code, 404
        )
        client.force_authenticate(self.platform_reviewer)
        self.assertEqual(client.get(url).status_code, 403)

    def test_pending_proposal_is_not_sampled_and_checker_is_excluded(self):
        _, decision = self.configure(checker=True)
        self.assertFalse(ReviewQualityAssignment.objects.exists())
        third = PlatformUser.objects.create_user(
            email="third-qa@example.test",
            password="SyntheticPassword123!",
            tenant=self.tenant,
            status="active",
        )
        self.member(self.tenant_case.queue_entry.queue, third)
        client = APIClient()
        client.force_authenticate(self.second)
        response = client.post(
            reverse(
                "manual-review-approval",
                kwargs={"verification_id": self.tenant_case.public_id},
            ),
            {"decision": "verified", "reason_code": "evidence_confirmed"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        sample = ReviewQualityAssignment.objects.get()
        self.assertEqual(sample.maker_id, self.tenant_reviewer.pk)
        self.assertEqual(sample.checker_id, self.second.pk)
        self.assertEqual(sample.reviewer_id, third.pk)
        self.assertEqual(
            client.get(
                reverse("review-quality-detail", kwargs={"sample_id": sample.public_id})
            ).status_code,
            404,
        )

    def test_revoked_availability_and_invalid_notes_cannot_complete_sample(self):
        self.configure()
        sample = ReviewQualityAssignment.objects.get()
        with self.assertRaises(ValidationError):
            complete_sample(
                sample,
                actor=self.second,
                outcome="rejected",
                reason_code="evidence_mismatch",
                notes="",
            )
        with self.assertRaises(ValidationError):
            complete_sample(
                sample,
                actor=self.second,
                outcome="rejected",
                reason_code="evidence_mismatch",
                notes="<script>bad</script>",
            )
        member = sample.queue.members.get(user=self.second)
        member.available = False
        member.save()
        with self.assertRaises(ValidationError):
            complete_sample(
                sample,
                actor=self.second,
                outcome="verified",
                reason_code="evidence_confirmed",
                notes="",
            )
        sample.refresh_from_db()
        self.assertIsNone(sample.completed_at)


class ReviewQualityRaceTests(TransactionTestCase):
    setUp = ReviewQualityTests.setUp
    _create_case = ReviewQualityTests._create_case
    queue = ReviewQualityTests.queue
    member = ReviewQualityTests.member
    configure = ReviewQualityTests.configure

    @skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
    def test_concurrent_disagreeing_assessments_commit_only_one_quality_outcome(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        from apps.audit.models import AuditEvent

        self.configure()
        sample = ReviewQualityAssignment.objects.get()
        ready = Barrier(2)

        def submit(outcome):
            close_old_connections()
            try:
                current = ReviewQualityAssignment.objects.get(pk=sample.pk)
                actor = PlatformUser.objects.get(pk=self.second.pk)
                ready.wait(timeout=15)
                try:
                    complete_sample(
                        current,
                        actor=actor,
                        outcome=outcome,
                        reason_code=(
                            "evidence_confirmed"
                            if outcome == "verified"
                            else "evidence_mismatch"
                        ),
                        notes="Independent assessment",
                    )
                    return "completed"
                except ValidationError:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, ["verified", "rejected"]))
        self.assertEqual(sorted(results), ["completed", "conflict"])
        self.assertEqual(
            AuditEvent.objects.filter(action="review_quality.completed").count(), 1
        )
        self.tenant_case.refresh_from_db()
        self.assertEqual(self.tenant_case.status, "verified")
