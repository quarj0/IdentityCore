from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.accounts.models import PlatformUserStatus
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)


def create_notification(
    *,
    tenant,
    recipient_type: str,
    recipient: str,
    channel: str,
    template_code: str,
    subject: str = "",
    body_preview: str = "",
) -> Notification:
    return Notification.objects.create(
        tenant=tenant,
        recipient_type=recipient_type,
        recipient=recipient,
        channel=channel,
        template_code=template_code,
        subject=subject,
        body_preview=body_preview,
        status=NotificationStatus.PENDING,
    )


def queue_verification_created_notifications(
    *, verification, verification_url: str
) -> list[Notification]:
    notifications: list[Notification] = []
    subject = verification.verification_subject
    if subject.email:
        notifications.append(
            create_notification(
                tenant=verification.tenant,
                recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
                recipient=subject.email,
                channel=NotificationChannel.EMAIL,
                template_code="verification.created",
                subject="Your verification is ready",
                body_preview=f"Use this link to continue your verification: {verification_url}",
            )
        )
    return notifications


def queue_verification_status_notifications(
    *, verification, decision: str, risk_level: str = ""
) -> list[Notification]:
    notifications: list[Notification] = []
    subject = verification.verification_subject
    status_subject_map = {
        "verified": "Your verification was approved",
        "rejected": "Your verification needs attention",
        "manual_review_required": "Your verification is under review",
        "cancelled": "Your verification was cancelled",
        "expired": "Your verification link has expired",
    }
    status_body_map = {
        "verified": f"Verification {verification.public_id} has been completed successfully.",
        "rejected": f"Verification {verification.public_id} could not be approved at this time.",
        "manual_review_required": (
            f"Verification {verification.public_id} needs additional review."
            + (f" Current risk level: {risk_level}." if risk_level else "")
        ),
        "cancelled": f"Verification {verification.public_id} has been cancelled.",
        "expired": f"Verification {verification.public_id} expired before completion.",
    }
    if subject.email and decision in status_subject_map:
        notifications.append(
            create_notification(
                tenant=verification.tenant,
                recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
                recipient=subject.email,
                channel=NotificationChannel.EMAIL,
                template_code=f"verification.{decision}",
                subject=status_subject_map[decision],
                body_preview=status_body_map[decision],
            )
        )

    if decision == "manual_review_required":
        platform_users = verification.tenant.platform_users.filter(
            status=PlatformUserStatus.ACTIVE
        )
        for user in platform_users:
            notifications.append(
                create_notification(
                    tenant=verification.tenant,
                    recipient_type=NotificationRecipientType.PLATFORM_USER,
                    recipient=user.email,
                    channel=NotificationChannel.EMAIL,
                    template_code="verification.manual_review_assigned",
                    subject="A verification needs manual review",
                    body_preview=(
                        f"Verification {verification.public_id} requires review."
                        + (f" Risk level: {risk_level}." if risk_level else "")
                    ),
                )
            )
    return notifications


def deliver_notification(notification: Notification) -> Notification:
    if notification.status != NotificationStatus.PENDING:
        return notification

    if notification.channel == NotificationChannel.EMAIL:
        send_mail(
            subject=notification.subject or "IdentityCore notification",
            message=notification.body_preview,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient],
            fail_silently=False,
        )
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.provider_reference = f"email:{notification.public_id}"
        notification.save(
            update_fields=["status", "sent_at", "provider_reference", "updated_at"]
        )
        return notification

    if notification.channel == NotificationChannel.IN_APP:
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.provider_reference = f"in_app:{notification.public_id}"
        notification.save(
            update_fields=["status", "sent_at", "provider_reference", "updated_at"]
        )
        return notification

    notification.status = NotificationStatus.CANCELLED
    notification.save(update_fields=["status", "updated_at"])
    return notification


def process_pending_notifications(*, limit: int = 50) -> int:
    processed = 0
    for notification in Notification.objects.filter(
        status=NotificationStatus.PENDING
    ).order_by("created_at")[:limit]:
        deliver_notification(notification)
        processed += 1
    return processed
