from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from apps.notifications.services import (
    deliver_notification,
    process_pending_notifications,
    queue_verification_created_notifications,
    queue_verification_status_notifications,
)
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class NotificationModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Kwame Mensah",
            email="kwame@example.com",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now(),
        )

    def test_create_pending_email_notification(self):
        notification = Notification.objects.create(
            tenant=self.tenant,
            recipient_type=NotificationRecipientType.PLATFORM_USER,
            recipient="owner@example.com",
            channel=NotificationChannel.EMAIL,
            template_code="verification.created",
            subject="Your verification is ready",
            body_preview="Open the verification link to continue.",
        )

        self.assertTrue(notification.public_id.startswith("ntf_"))
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertIsNone(notification.sent_at)

    def test_sent_notification_requires_sent_timestamp(self):
        with self.assertRaises(ValidationError) as exc:
            Notification.objects.create(
                tenant=self.tenant,
                recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
                recipient="subject@example.com",
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT,
            )

        self.assertIn("sent_at", exc.exception.message_dict)

    def test_non_sent_notification_cannot_include_sent_timestamp(self):
        with self.assertRaises(ValidationError) as exc:
            Notification.objects.create(
                tenant=self.tenant,
                recipient_type=NotificationRecipientType.PLATFORM_USER,
                recipient="owner@example.com",
                channel=NotificationChannel.IN_APP,
                status=NotificationStatus.FAILED,
                sent_at=timezone.now(),
            )

        self.assertIn("sent_at", exc.exception.message_dict)

    def test_queue_verification_created_notification_for_subject_email(self):
        notifications = queue_verification_created_notifications(
            verification=self.verification,
            verification_url="http://localhost:8000/api/v1/verification-sessions/ses_123",
        )

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].template_code, "verification.created")
        self.assertEqual(notifications[0].recipient, "kwame@example.com")

    def test_queue_manual_review_notifications_for_subject_and_platform_users(self):
        notifications = queue_verification_status_notifications(
            verification=self.verification,
            decision=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            risk_level="high",
        )

        self.assertEqual(len(notifications), 2)
        self.assertSetEqual(
            {notification.recipient for notification in notifications},
            {"kwame@example.com", "owner@example.com"},
        )

    def test_deliver_email_notification_marks_sent_and_writes_outbox(self):
        notification = Notification.objects.create(
            tenant=self.tenant,
            recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
            recipient="kwame@example.com",
            channel=NotificationChannel.EMAIL,
            template_code="verification.verified",
            subject="Approved",
            body_preview="Your verification is complete.",
        )

        deliver_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, NotificationStatus.SENT)
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["kwame@example.com"])

    def test_process_pending_notifications_delivers_in_creation_order(self):
        first = Notification.objects.create(
            tenant=self.tenant,
            recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
            recipient="first@example.com",
            channel=NotificationChannel.EMAIL,
            template_code="verification.created",
            subject="First",
            body_preview="First notification.",
        )
        second = Notification.objects.create(
            tenant=self.tenant,
            recipient_type=NotificationRecipientType.PLATFORM_USER,
            recipient="second@example.com",
            channel=NotificationChannel.EMAIL,
            template_code="verification.manual_review_assigned",
            subject="Second",
            body_preview="Second notification.",
        )

        processed = process_pending_notifications(limit=10)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(processed, 2)
        self.assertEqual(first.status, NotificationStatus.SENT)
        self.assertEqual(second.status, NotificationStatus.SENT)
        self.assertEqual(
            [message.to[0] for message in mail.outbox],
            ["first@example.com", "second@example.com"],
        )
