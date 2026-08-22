from unittest.mock import Mock, patch

from django.test import TestCase

from apps.notifications.services import dispatch_notification_delivery


class NotificationPostCommitDispatchTests(TestCase):
    @patch(
        "apps.notifications.tasks.deliver_notification_task.delay",
        side_effect=RuntimeError("broker unavailable"),
    )
    def test_broker_failure_does_not_escape_post_commit_callback(self, mock_delay):
        notification = Mock(public_id="ntf_POST_COMMIT")

        with self.captureOnCommitCallbacks(execute=True):
            dispatch_notification_delivery(notification)

        mock_delay.assert_called_once_with("ntf_POST_COMMIT")
