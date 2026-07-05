from django.conf import settings
from django.test import SimpleTestCase

from apps.biometrics.tasks import process_verification_biometrics_task
from apps.identity_documents.tasks import process_identity_document_task
from apps.notifications.tasks import deliver_notification_task, process_pending_notifications_task
from apps.webhooks.tasks import deliver_webhook_event_task, process_pending_webhook_events_task


class CeleryConfigurationTests(SimpleTestCase):
    def test_default_queue_is_explicit_for_general_background_work(self):
        self.assertEqual(settings.CELERY_TASK_DEFAULT_QUEUE, "default")
        self.assertEqual(settings.CELERY_TASK_DEFAULT_ROUTING_KEY, "default")

    def test_celery_beat_schedule_registers_webhook_and_notification_processors(self):
        self.assertIn("process-pending-webhooks", settings.CELERY_BEAT_SCHEDULE)
        self.assertIn("process-pending-notifications", settings.CELERY_BEAT_SCHEDULE)
        self.assertEqual(
            settings.CELERY_BEAT_SCHEDULE["process-pending-webhooks"]["task"],
            "apps.webhooks.tasks.process_pending_webhook_events_task",
        )
        self.assertEqual(
            settings.CELERY_BEAT_SCHEDULE["process-pending-notifications"]["task"],
            "apps.notifications.tasks.process_pending_notifications_task",
        )

    def test_celery_routes_use_dedicated_lightweight_queues(self):
        self.assertEqual(settings.CELERY_TASK_ROUTES[process_verification_biometrics_task.name]["queue"], "ai_processing")
        self.assertEqual(settings.CELERY_TASK_ROUTES[process_identity_document_task.name]["queue"], "ai_processing")
        self.assertEqual(settings.CELERY_TASK_ROUTES[process_pending_webhook_events_task.name]["queue"], "webhooks")
        self.assertEqual(settings.CELERY_TASK_ROUTES[deliver_webhook_event_task.name]["queue"], "webhooks")
        self.assertEqual(
            settings.CELERY_TASK_ROUTES[process_pending_notifications_task.name]["queue"],
            "notifications",
        )
        self.assertEqual(settings.CELERY_TASK_ROUTES[deliver_notification_task.name]["queue"], "notifications")
