"""Serialize notification admission/finalization with subject privacy deletion."""

from django.db import transaction
from django.db.models import Q

from apps.audit.services import lock_audit_chain
from apps.notifications.models import (
    Notification,
    NotificationRecipientType,
    NotificationStatus,
)


def scrub_notification(notification):
    notification.recipient = "deleted"
    notification.subject = ""
    notification.body_preview = ""
    notification.delivery_json = {}
    notification.provider_reference = ""
    if notification.status != NotificationStatus.SENT:
        notification.status = NotificationStatus.CANCELLED
        notification.sent_at = None
    notification.save(
        update_fields=[
            "verification_subject",
            "recipient",
            "subject",
            "body_preview",
            "delivery_json",
            "provider_reference",
            "status",
            "sent_at",
            "updated_at",
        ]
    )
    return notification


@transaction.atomic
def scrub_subject_notifications(subject):
    lock_audit_chain(subject.tenant_id)
    contacts = Q(pk__in=[])
    if subject.email:
        contacts |= Q(recipient__iexact=subject.email)
    if subject.phone_number:
        contacts |= Q(recipient=subject.phone_number)
    rows = (
        Notification.objects.select_for_update(of=("self",))
        .filter(
            tenant_id=subject.tenant_id,
            recipient_type=NotificationRecipientType.VERIFICATION_SUBJECT,
        )
        .filter(
            Q(verification_subject=subject)
            | (Q(verification_subject__isnull=True) & contacts)
        )
    )
    count = 0
    for notification in rows.order_by("pk"):
        # Bind legacy matches so an admitted stale delivery cannot restore its data.
        notification.verification_subject = subject
        scrub_notification(notification)
        count += 1
    return count


def _locked_notification(notification):
    if notification.tenant_id is not None:
        lock_audit_chain(notification.tenant_id)
    current = (
        Notification.objects.select_for_update(of=("self",))
        .select_related("verification_subject")
        .get(pk=notification.pk)
    )
    if current.tenant_id != notification.tenant_id:
        raise ValueError("Notification ownership changed.")
    return current


def _deleted_subject(notification):
    return (
        notification.verification_subject_id is not None
        and notification.verification_subject.deleted_at is not None
    )


@transaction.atomic
def delivery_snapshot(notification):
    current = _locked_notification(notification)
    if _deleted_subject(current):
        return scrub_notification(current), False
    return current, current.status == NotificationStatus.PENDING


@transaction.atomic
def persist_delivery_result(notification, *, update_fields):
    current = _locked_notification(notification)
    if _deleted_subject(current):
        scrub_notification(current)
    elif current.status == NotificationStatus.PENDING:
        for name in update_fields:
            if name != "updated_at":
                setattr(current, name, getattr(notification, name))
        current.save(update_fields=update_fields)
    # Return the fresh persisted result to callers, including cancellation/erasure
    # that committed while the already-admitted external request was in flight.
    notification.__dict__.update(current.__dict__)
    notification._state.fields_cache.clear()
