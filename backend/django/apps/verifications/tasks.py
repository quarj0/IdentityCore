from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.biometrics.models import SelfieCaptureStatus
from apps.document_captures.models import DocumentCaptureStatus
from apps.notifications.services import queue_verification_status_notifications
from apps.verifications.models import (
    Verification,
    VerificationSession,
    VerificationSessionStatus,
    VerificationStatus,
)
from apps.webhooks.services import queue_webhook_events


EXPIRABLE_VERIFICATION_STATUSES = {
    VerificationStatus.CREATED,
    VerificationStatus.PENDING_CONSENT,
    VerificationStatus.IN_PROGRESS,
    VerificationStatus.AWAITING_DOCUMENT,
    VerificationStatus.AWAITING_SELFIE,
    VerificationStatus.PROCESSING,
    VerificationStatus.MANUAL_REVIEW_REQUIRED,
}

EXPIRABLE_SESSION_STATUSES = {
    VerificationSessionStatus.CREATED,
    VerificationSessionStatus.ACTIVE,
}

RETENTION_COMPLETED_VERIFICATION_STATUSES = {
    VerificationStatus.VERIFIED,
    VerificationStatus.REJECTED,
    VerificationStatus.CANCELLED,
    VerificationStatus.EXPIRED,
    VerificationStatus.FAILED,
}


@shared_task(queue="retention")
def expire_pending_verifications_task(limit: int = 100) -> int:
    now = timezone.now()
    expired = 0
    verifications = (
        Verification.objects.select_related("tenant", "verification_subject")
        .filter(status__in=EXPIRABLE_VERIFICATION_STATUSES, expires_at__lte=now)
        .order_by("expires_at")[:limit]
    )
    for verification in verifications:
        verification.status = VerificationStatus.EXPIRED
        verification.completed_at = now
        verification.save(update_fields=["status", "completed_at", "updated_at"])
        verification.sessions.filter(status__in=EXPIRABLE_SESSION_STATUSES).update(
            status=VerificationSessionStatus.EXPIRED,
            updated_at=now,
        )
        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action="verification.expired",
            target_type="verification",
            target_id=verification.public_id,
        )
        queue_webhook_events(
            tenant=verification.tenant,
            event_type="verification.expired",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
        )
        queue_verification_status_notifications(
            verification=verification,
            decision=VerificationStatus.EXPIRED,
        )
        expired += 1
    return expired


@shared_task(queue="retention")
def cleanup_expired_verification_sessions_task(limit: int = 200) -> int:
    now = timezone.now()
    updated = VerificationSession.objects.filter(
        status__in=EXPIRABLE_SESSION_STATUSES,
        expires_at__lte=now,
    ).order_by("expires_at")[:limit]
    session_ids = [session.id for session in updated]
    if not session_ids:
        return 0
    return VerificationSession.objects.filter(id__in=session_ids).update(
        status=VerificationSessionStatus.EXPIRED,
        updated_at=now,
    )


@shared_task(queue="retention")
def cleanup_retained_media_task(limit: int = 100) -> int:
    now = timezone.now()
    cleaned = 0
    verifications = (
        Verification.objects.select_related("tenant")
        .filter(
            status__in=RETENTION_COMPLETED_VERIFICATION_STATUSES,
            completed_at__isnull=False,
        )
        .order_by("completed_at")[:limit]
    )
    for verification in verifications:
        retention_days = int(
            (verification.policy_snapshot_json or {}).get("media_retention_days", 30)
        )
        cutoff = verification.completed_at + timedelta(days=retention_days)
        if cutoff > now:
            continue

        media_deleted = False

        for identity_document in verification.identity_documents.prefetch_related(
            "captures"
        ):
            for capture in identity_document.captures.filter(deleted_at__isnull=True):
                capture.status = DocumentCaptureStatus.DELETED
                capture.deleted_at = now
                capture.save(update_fields=["status", "deleted_at", "updated_at"])
                media_deleted = True

        for selfie in verification.selfie_captures.filter(deleted_at__isnull=True):
            selfie.status = SelfieCaptureStatus.DELETED
            selfie.deleted_at = now
            selfie.save(update_fields=["status", "deleted_at", "updated_at"])
            media_deleted = True

        if not media_deleted:
            continue

        record_audit_event(
            tenant=verification.tenant,
            action="retention.media_deleted",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"media_retention_days": retention_days},
        )
        cleaned += 1
    return cleaned
