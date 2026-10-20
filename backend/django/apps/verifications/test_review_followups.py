from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.accounts.models import PlatformUser
from apps.access_control.test_helpers import grant_review_permission
from apps.audit.models import AuditEvent
from apps.notifications.models import Notification
from apps.verifications import tests as fixtures
from apps.verifications.models import Verification, VerificationStatus
from apps.verifications.serializers import serialize_verification
from apps.verifications.transitions import transition_verification


class ReviewLifecycleFollowupTests(APITestCase):
    setUp = fixtures.VerificationWorkflowTests.setUp
    auth_headers = fixtures.VerificationWorkflowTests.auth_headers

    def case(self, **kwargs):
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Synthetic reviewed subject", email="subject@example.test"
            ),
            purpose="Review regression",
            expires_at=timezone.now() + timedelta(hours=1),
            **kwargs,
        )

    def test_repeated_cancel_does_not_duplicate_audit_or_lifecycle_outbox(self):
        case = self.case(status=VerificationStatus.PENDING_CONSENT)
        url = reverse("verification-cancel", kwargs={"verification_id": case.public_id})
        with patch("apps.verifications.views.queue_webhook_events") as webhooks:
            for _ in range(2):
                response = self.client.post(
                    url, {}, format="json", **self.auth_headers()
                )
                self.assertEqual(response.status_code, 200)
        webhooks.assert_called_once()
        self.assertEqual(
            AuditEvent.objects.filter(
                target_id=case.public_id, action="verification.cancelled"
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                tenant=self.tenant, template_code="verification.cancelled"
            ).count(),
            1,
        )

    def test_repeated_cancel_repairs_legacy_timestamps_without_changing_known_time(
        self,
    ):
        known = timezone.now() - timedelta(days=1)
        for cancelled, completed in ((None, known), (known, None), (None, None)):
            case = self.case(
                status=VerificationStatus.CANCELLED,
                cancelled_at=cancelled,
                completed_at=completed,
            )
            before = timezone.now()
            current, changed = transition_verification(
                case, VerificationStatus.CANCELLED
            )
            self.assertFalse(changed)
            self.assertEqual(current.cancelled_at, current.completed_at)
            if cancelled or completed:
                self.assertEqual(current.cancelled_at, known)
            else:
                self.assertGreaterEqual(current.cancelled_at, before)
            self.assertEqual(case.cancelled_at, current.cancelled_at)
            again, changed = transition_verification(case, VerificationStatus.CANCELLED)
            self.assertFalse(changed)
            self.assertEqual(again.cancelled_at, current.cancelled_at)

    def test_direct_failed_decision_dispatches_lifecycle_once_with_replay(self):
        case = self.case(status=VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.client.force_authenticate(self.user)
        with patch("apps.verifications.views.queue_webhook_events") as webhooks:
            for _ in range(2):
                response = self.client.post(
                    reverse(
                        "manual-review-decision",
                        kwargs={"verification_id": case.public_id},
                    ),
                    {"decision": "failed", "reason_code": "evidence_unavailable"},
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="synthetic-failed-review",
                )
                self.assertEqual(response.status_code, 200)
        webhooks.assert_called_once()
        self.assertEqual(webhooks.call_args.kwargs["event_type"], "verification.failed")
        self.assertEqual(
            Notification.objects.filter(
                tenant=self.tenant, template_code="verification.failed"
            ).count(),
            1,
        )

    def test_current_caller_approval_hint_excludes_maker_creator_subject_and_unprivileged(
        self,
    ):
        case = self.case(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            policy_snapshot_json={"maker_checker_required": True},
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse(
                "manual-review-decision", kwargs={"verification_id": case.public_id}
            ),
            {"decision": "verified", "reason_code": "confirmed"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="synthetic-proposal",
        )
        self.assertEqual(response.status_code, 202)
        checker = PlatformUser.objects.create_user(
            email="checker@example.test",
            password="StrongPassword123!",
            status="active",
            tenant=self.tenant,
        )
        grant_review_permission(checker)

        def hint(user):
            return serialize_verification(case, request=SimpleNamespace(user=user))[
                "decision"
            ]["can_approve"]

        self.assertFalse(hint(self.user))
        from config.graphql_types import to_verification_node

        node = to_verification_node(
            serialize_verification(case, request=SimpleNamespace(user=checker))
        )
        self.assertTrue(node.decision.can_approve)
        self.assertTrue(hint(checker))
        self.assertFalse(hint(None))
        case.created_by = checker
        self.assertFalse(hint(checker))
        case.created_by = None
        checker.email = case.verification_subject.email.upper()
        self.assertFalse(hint(checker))
        outsider = PlatformUser.objects.create_user(
            email="unprivileged@example.test",
            password="StrongPassword123!",
            status="active",
            tenant=self.tenant,
        )
        self.assertFalse(hint(outsider))
