from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.notifications.models import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class NotificationModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
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
