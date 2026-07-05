from celery import shared_task

from apps.notifications.services import deliver_notification, process_pending_notifications
from apps.notifications.models import Notification


@shared_task
def process_pending_notifications_task(limit: int = 50) -> int:
    return process_pending_notifications(limit=limit)


@shared_task
def deliver_notification_task(notification_id: str) -> str:
    notification = Notification.objects.get(public_id=notification_id)
    deliver_notification(notification)
    notification.refresh_from_db()
    return notification.status
