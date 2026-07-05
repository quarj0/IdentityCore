from apps.notifications.models import Notification


def serialize_notification(notification: Notification) -> dict:
    return {
        "id": notification.public_id,
        "recipient_type": notification.recipient_type,
        "recipient": notification.recipient,
        "channel": notification.channel,
        "template_code": notification.template_code,
        "status": notification.status,
        "subject": notification.subject,
        "body_preview": notification.body_preview,
        "provider_reference": notification.provider_reference,
        "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
        "created_at": notification.created_at.isoformat(),
        "updated_at": notification.updated_at.isoformat(),
    }
