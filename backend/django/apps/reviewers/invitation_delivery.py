"""Platform-only encrypted invitation outbox; no tenant email credentials."""

from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.notifications.models import Notification
from apps.notifications.services import enqueue_notification_delivery


def queue_platform_invitation(invitation, raw):
    base = settings.PLATFORM_INVITATION_BASE_URL
    url = urlsplit(base)
    if (
        not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.scheme not in {"http", "https"}
        or (url.scheme != "https" and not settings.DEBUG)
    ):
        raise ValidationError(
            "Platform invitation delivery URL must be configured safely."
        )
    notification = Notification.objects.create(
        tenant=None,
        recipient_type="platform_user",
        recipient=invitation.email,
        channel="email",
        template_code="platform_admin.invitation",
        subject="Your IdentityCore platform administrator invitation",
        body_preview="A single-use platform invitation was queued for this recipient.",
        delivery_json={
            "platform_invitation": invitation.public_id,
            "token": raw,
            "body": "Accept your IdentityCore platform administrator invitation: "
            + base
            + "#"
            + urlencode({"token": raw}),
        },
    )
    enqueue_notification_delivery(notification)
