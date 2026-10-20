from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.notifications import tests as fixtures
from apps.notifications.models import Notification
from apps.notifications.services import (
    create_notification,
    deliver_notification,
    queue_verification_created_notifications,
)
from apps.verification_subjects.services import request_subject_deletion


class SubjectNotificationPrivacyTests(TestCase):
    setUp = fixtures.NotificationModelTests.setUp

    def _notification(self, *, bound=True, recipient=None, status="pending"):
        notification = create_notification(
            tenant=self.tenant,
            recipient_type="verification_subject",
            recipient=recipient or self.subject.email,
            channel="email",
            template_code="verification.created",
            subject="Private subject",
            body_preview="Private link",
            verification_subject=self.subject if bound else None,
        )
        notification.delivery_json = {"private": "value"}
        notification.status = status
        notification.sent_at = timezone.now() if status == "sent" else None
        notification.save()
        return notification

    def test_deletion_scrubs_bound_and_legacy_subject_messages_without_touching_other_recipients(
        self,
    ):
        bound = self._notification()
        legacy = self._notification(bound=False)
        historical = self._notification(status="sent")
        other = self._notification(bound=False, recipient="other@example.test")
        from apps.verification_subjects.models import VerificationSubject

        second = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Other", email=self.subject.email
        )
        bound_other = create_notification(
            tenant=self.tenant,
            recipient_type="verification_subject",
            recipient=second.email,
            verification_subject=second,
            channel="email",
            template_code="verification.created",
        )
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant

        foreign_org = Organization.objects.create(
            name="Foreign", slug="foreign-privacy"
        )
        foreign_tenant = Tenant.objects.create(
            organization=foreign_org, name="Foreign", slug="foreign-privacy"
        )
        foreign = create_notification(
            tenant=foreign_tenant,
            recipient_type="verification_subject",
            recipient=self.subject.email,
            channel="email",
            template_code="verification.created",
        )
        stale = Notification.objects.get(pk=legacy.pk)
        result = request_subject_deletion(subject=self.subject)
        self.assertEqual(result["notifications_anonymized"], 3)
        for notification in (bound, legacy, historical):
            notification.refresh_from_db()
            self.assertEqual(notification.recipient, "deleted")
            self.assertEqual(notification.subject, "")
            self.assertEqual(notification.body_preview, "")
            self.assertEqual(notification.delivery_json, {})
            self.assertEqual(notification.provider_reference, "")
            self.assertEqual(notification.verification_subject_id, self.subject.pk)
        self.assertEqual(historical.status, "sent")
        self.assertIsNotNone(historical.sent_at)
        self.assertEqual(bound.status, "cancelled")
        other.refresh_from_db()
        self.assertEqual(other.status, "pending")
        self.assertEqual(other.recipient, "other@example.test")
        for preserved in (bound_other, foreign):
            preserved.refresh_from_db()
            self.assertEqual(preserved.status, "pending")
            self.assertEqual(preserved.recipient, self.subject.email)
        with patch("apps.notifications.services.get_notification_provider") as provider:
            deliver_notification(stale)
        provider.assert_not_called()
        self.assertEqual(stale.status, "cancelled")

    def test_stale_queue_caller_cannot_recreate_personal_data_after_deletion(self):
        # The verification retains a cached pre-erasure subject with its email.
        cached = self.verification.verification_subject
        self.assertTrue(cached.email)
        request_subject_deletion(subject=self.subject)
        with patch(
            "apps.notifications.tasks.deliver_notification_task.delay"
        ) as dispatch:
            with self.captureOnCommitCallbacks(execute=True):
                messages = queue_verification_created_notifications(
                    verification=self.verification,
                    verification_url="https://portal.example.test/private-fragment",
                )
        dispatch.assert_not_called()
        for notification in messages:
            self.assertEqual(notification.status, "cancelled")
            self.assertEqual(notification.recipient, "deleted")
            self.assertEqual(notification.body_preview, "")

    def test_subject_binding_cannot_cross_tenant_or_recipient_type(self):
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                tenant=self.tenant,
                verification_subject=self.subject,
                recipient_type="platform_user",
                recipient="user@example.test",
                channel="email",
            )
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                tenant=None,
                verification_subject=self.subject,
                recipient_type="verification_subject",
                recipient=self.subject.email,
                channel="email",
            )
