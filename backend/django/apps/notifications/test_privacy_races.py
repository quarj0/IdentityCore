from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless
from unittest.mock import patch
from types import SimpleNamespace

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.utils import timezone

from apps.audit.services import verify_audit_chain
from apps.notifications import tests as fixtures
from apps.notifications.models import Notification
from apps.notifications.providers import NotificationDeliveryResult
from apps.notifications.services import create_notification, deliver_notification
from apps.verification_subjects.services import request_subject_deletion


@skipUnless(
    connection.vendor == "postgresql", "Notification privacy races need real row locks"
)
class SubjectNotificationDeliveryRaceTests(TransactionTestCase):
    setUp = fixtures.NotificationModelTests.setUp

    def _race(self, bound):
        notification = create_notification(
            tenant=self.tenant,
            recipient_type="verification_subject",
            recipient=self.subject.email,
            verification_subject=self.subject if bound else None,
            channel="email",
            template_code="verification.created",
            body_preview="Private link",
        )
        sending, deleted = Event(), Event()

        def send(row):
            self.assertFalse(connection.in_atomic_block)
            self.assertEqual(row.recipient, self.subject.email)
            sending.set()
            if not deleted.wait(10):
                raise AssertionError(
                    "Deletion could not commit during the admitted send"
                )
            return NotificationDeliveryResult(
                provider_reference="private-delivery-reference", sent_at=timezone.now()
            )

        def deliver():
            close_old_connections()
            try:
                current = Notification.objects.get(pk=notification.pk)
                deliver_notification(current)
                return current
            finally:
                close_old_connections()

        with patch(
            "apps.notifications.services.get_notification_provider",
            return_value=SimpleNamespace(deliver=send),
        ):
            with ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(deliver)
                self.assertTrue(sending.wait(10))
                try:
                    self.assertEqual(
                        request_subject_deletion(subject=self.subject)["status"],
                        "completed",
                    )
                finally:
                    deleted.set()
                returned = result.result(timeout=15)
        notification.refresh_from_db()
        self.assertEqual(notification.status, "cancelled")
        self.assertEqual(returned.status, "cancelled")
        self.assertEqual(notification.recipient, "deleted")
        self.assertEqual(notification.body_preview, "")
        self.assertEqual(notification.provider_reference, "")
        self.assertEqual(notification.delivery_json, {})
        self.assertIsNone(notification.sent_at)
        self.assertEqual(notification.verification_subject_id, self.subject.pk)
        self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk), (True, ""))

    def test_bound_admitted_delivery_cannot_restore_erased_fields(self):
        self._race(True)

    def test_legacy_admitted_delivery_cannot_restore_erased_fields(self):
        self._race(False)
