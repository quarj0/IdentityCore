from django.db import transaction
from django.utils import timezone

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from apps.notifications.providers import (
    NotificationDeliveryError,
    NotificationProviderNotConfigured,
    get_notification_provider,
)


def create_notification(
    *,
    tenant=None,
    tenant_id: str | None = None,
    recipient_type: str,
    recipient: str,
    channel: str,
    template_code: str,
    subject: str = "",
    body_preview: str = "",
) -> Notification:
    if tenant_id is None:
        tenant_id = getattr(tenant, "pk", None)
    return Notification.objects.create(
        tenant_id=tenant_id,
        recipient_type=recipient_type,
        recipient=recipient,
        channel=channel,
        template_code=template_code,
        subject=subject,
        body_preview=body_preview,
        status=NotificationStatus.PENDING,
    )


def schedule_notification_delivery(notification: Notification) -> None:
    from apps.notifications.tasks import deliver_notification_task

    transaction.on_commit(
        lambda: deliver_notification_task.delay(notification.public_id)
    )


def queue_verification_created_notifications(
    *, verification, verification_url: str
) -> list[Notification]:
    notifications: list[Notification] = []
    subject = verification.verification_subject
    if subject.email:
        notifications.append(
            create_notification(
                tenant_id=verification.tenant_id,
                recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
                recipient=subject.email,
                channel=NotificationChannel.EMAIL,
                template_code="verification.created",
                subject="Your verification is ready",
                body_preview=f"Use this link to continue your verification: {verification_url}",
            )
        )
        schedule_notification_delivery(notifications[-1])
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
                tenant_id=verification.tenant_id,
                recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
                recipient=subject.email,
                channel=NotificationChannel.EMAIL,
                template_code=f"verification.{decision}",
                subject=status_subject_map[decision],
                body_preview=status_body_map[decision],
            )
        )
        schedule_notification_delivery(notifications[-1])

    if decision == "manual_review_required":
        platform_users = PlatformUser.objects.filter(
            tenant_id=verification.tenant_id,
            status=PlatformUserStatus.ACTIVE,
        )
        for user in platform_users:
            notifications.append(
                create_notification(
                    tenant_id=verification.tenant_id,
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
            schedule_notification_delivery(notifications[-1])
    return notifications


def deliver_notification(notification: Notification) -> Notification:
    if notification.status != NotificationStatus.PENDING:
        return notification

    try:
        provider = get_notification_provider(notification)
        result = provider.deliver(notification)
    except NotificationProviderNotConfigured:
        notification.status = NotificationStatus.FAILED
        notification.provider_reference = f"{notification.channel}:not_configured"
        notification.save(update_fields=["status", "provider_reference", "updated_at"])
        return notification
    except NotificationDeliveryError:
        notification.status = NotificationStatus.FAILED
        notification.provider_reference = f"{notification.channel}:delivery_failed"
        notification.save(update_fields=["status", "provider_reference", "updated_at"])
        return notification
    except Exception:
        notification.status = NotificationStatus.FAILED
        notification.provider_reference = f"{notification.channel}:unexpected_error"
        notification.save(update_fields=["status", "provider_reference", "updated_at"])
        return notification

    notification.status = NotificationStatus.SENT
    notification.sent_at = result.sent_at or timezone.now()
    notification.provider_reference = result.provider_reference
    notification.save(
        update_fields=["status", "sent_at", "provider_reference", "updated_at"]
    )
    return notification


def process_pending_notifications(*, limit: int = 50) -> int:
    processed = 0
    with transaction.atomic():
        pending_ids = list(
            Notification.objects.select_for_update()
            .filter(status=NotificationStatus.PENDING)
            .order_by("created_at")
            .values_list("id", flat=True)[:limit]
        )
    for notification in Notification.objects.filter(id__in=pending_ids).order_by(
        "created_at"
    ):
        deliver_notification(notification)
        processed += 1
    return processed
