from celery import shared_task

from apps.notifications.services import (
    deliver_notification,
    process_pending_notifications,
)
from apps.notifications.models import Notification
from common.authorization import ServicePrincipal, require_service_access

NOTIFICATION_WORKER = ServicePrincipal(
    name="notification-worker",
    allowed_actions=frozenset({"notification.deliver", "notification.process_pending"}),
    allow_cross_tenant=True,
)


@shared_task(queue="notifications")
def process_pending_notifications_task(limit: int = 50) -> int:
    require_service_access(NOTIFICATION_WORKER, action="notification.process_pending")
    return process_pending_notifications(limit=limit)


@shared_task(queue="notifications")
def deliver_notification_task(notification_id: str) -> str:
    notification = Notification.objects.get(public_id=notification_id)
    require_service_access(
        NOTIFICATION_WORKER,
        action="notification.deliver",
        resource=notification,
    )
    deliver_notification(notification)
    notification.refresh_from_db()
    return notification.status
