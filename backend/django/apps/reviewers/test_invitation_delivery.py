from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.notifications.models import Notification
from apps.notifications.services import deliver_notification
from apps.notifications.providers import NotificationDeliveryError
from apps.reviewers.models import PlatformAdminInvitation
from apps.reviewers import test_historical_admin_controls as fixtures


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PLATFORM_INVITATION_BASE_URL="https://admin.example.test/accept-invitation",
)
class PlatformInvitationDeliveryTests(APITestCase):
    setUp = fixtures.HistoricalPlatformAdminControlTests.setUp
    graphql = fixtures.HistoricalPlatformAdminControlTests.graphql
    invite = fixtures.HistoricalPlatformAdminControlTests.invite

    def test_invitation_has_encrypted_durable_platform_email_and_safe_fragment(self):
        result = self.invite()
        self.assertIsNone(result.errors, result.errors)
        invitation = PlatformAdminInvitation.objects.get(
            email="replacement@example.test"
        )
        notification = Notification.objects.get(
            template_code="platform_admin.invitation"
        )
        delivery = notification.delivery_json
        self.assertEqual(notification.tenant_id, None)
        self.assertEqual(
            PlatformAdminInvitation.digest_token(delivery["token"]),
            invitation.token_hash,
        )
        self.assertNotIn(delivery["token"], notification.body_preview)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT delivery_json FROM notifications_notification WHERE id=%s",
                [notification.pk],
            )
            stored = str(cursor.fetchone()[0])
        self.assertNotIn(delivery["token"], stored)
        with patch(
            "apps.notifications.providers.get_notification_provider_assignment"
        ) as tenant_assignment:
            deliver_notification(notification)
        tenant_assignment.assert_not_called()
        self.assertEqual(notification.status, "sent")
        self.assertEqual(notification.delivery_json, {})
        self.assertIn(
            "https://admin.example.test/accept-invitation#token=", mail.outbox[0].body
        )
        self.assertNotIn("?token=", mail.outbox[0].body)

    def test_malformed_email_and_unsupported_limited_role_do_not_create_invites(self):
        for email, role in [
            ("not-an-email", "Platform Admin"),
            ("admin@example.test", "read-only"),
            ("admin@example.test", "Security Admin"),
        ]:
            result = self.graphql(
                "mutation($email:String!,$role:String!){invitePlatformAdmin(email:$email,roleName:$role){invitation{id}}}",
                {"email": email, "role": role},
            )
            self.assertTrue(result.errors)
        self.assertFalse(PlatformAdminInvitation.objects.exists())
        self.assertFalse(Notification.objects.exists())

    def test_revoked_inviter_cancels_queued_email_and_clears_credential(self):
        self.invite()
        self.actor.status = "inactive"
        self.actor.save(update_fields=["status", "updated_at"])
        notification = Notification.objects.get()
        deliver_notification(notification)
        self.assertEqual(notification.status, "cancelled")
        self.assertEqual(notification.delivery_json, {})
        self.assertEqual(len(mail.outbox), 0)

    def test_failed_delivery_can_be_replaced_with_a_new_single_use_credential(self):
        self.invite()
        old = PlatformAdminInvitation.objects.get()
        notification = Notification.objects.get()
        with patch(
            "apps.notifications.services.get_notification_provider",
            side_effect=NotificationDeliveryError,
        ):
            deliver_notification(notification)
        self.assertEqual(notification.status, "failed")
        result = self.invite()
        self.assertIsNone(result.errors, result.errors)
        old.refresh_from_db()
        self.assertEqual(old.status, "revoked")
        new = PlatformAdminInvitation.objects.get(status="pending")
        self.assertNotEqual(new.token_hash, old.token_hash)
        self.assertEqual(Notification.objects.filter(status="pending").count(), 1)

    def test_null_tenant_is_not_available_for_arbitrary_notifications(self):
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                tenant=None,
                channel="email",
                recipient_type="platform_user",
                recipient="synthetic@example.test",
                template_code="arbitrary",
            )
