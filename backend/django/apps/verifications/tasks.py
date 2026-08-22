from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.biometrics.models import SelfieCaptureStatus
from apps.document_captures.models import DocumentCaptureStatus
from apps.verifications.evidence_commit import (
    schedule_verification_evidence_report_after_commit,
)
from common.storage import (
    delete_object,
    get_object_storage_media_bucket_name,
)
from apps.notifications.services import queue_verification_status_notifications
from apps.verifications.models import (
    Verification,
    RetentionLegalHold,
    VerificationSession,
    VerificationSessionStatus,
    VerificationStatus,
)
from apps.verifications.processing_jobs import recover_stale_processing_jobs
from apps.verifications.transitions import transition_verification
from apps.webhooks.services import queue_webhook_events
from common.authorization import ServicePrincipal, require_service_access

VERIFICATION_MAINTENANCE_WORKER = ServicePrincipal(
    name="verification-maintenance-worker",
    allowed_actions=frozenset(
        {
            "verification.expire",
            "verification.cleanup_sessions",
            "verification.cleanup_media",
            "verification.recover_processing",
        }
    ),
    allow_cross_tenant=True,
)


@shared_task(queue="retention")
def recover_stale_processing_jobs_task(limit: int = 100) -> dict[str, int]:
    require_service_access(
        VERIFICATION_MAINTENANCE_WORKER,
        action="verification.recover_processing",
    )
    recovered, exhausted = recover_stale_processing_jobs(limit=limit)
    return {"recovered": recovered, "exhausted": exhausted}


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


def _has_active_retention_hold(verification: Verification, now) -> bool:
    return (
        RetentionLegalHold.objects.filter(
            tenant_id=verification.tenant_id,
            verification_id__in=[None, verification.id],
            released_at__isnull=True,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        .exists()
    )


@transaction.atomic
def _expire_pending_verification(verification_id: int, now) -> bool:
    verification = (
        Verification.objects.select_for_update()
        .select_related("tenant", "verification_subject")
        .get(pk=verification_id)
    )
    verification, changed = transition_verification(
        verification,
        VerificationStatus.EXPIRED,
        completed_at=now,
    )
    if not changed:
        return False
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
    schedule_verification_evidence_report_after_commit(verification)
    return True


@shared_task(queue="retention")
def expire_pending_verifications_task(limit: int = 100) -> int:
    require_service_access(
        VERIFICATION_MAINTENANCE_WORKER, action="verification.expire"
    )
    now = timezone.now()
    expired = 0
    verifications = (
        Verification.objects.select_related("tenant", "verification_subject")
        .filter(status__in=EXPIRABLE_VERIFICATION_STATUSES, expires_at__lte=now)
        .order_by("expires_at")[:limit]
    )
    for verification in verifications:
        if _expire_pending_verification(verification.pk, now):
            expired += 1
    return expired


@shared_task(queue="retention")
def cleanup_expired_verification_sessions_task(limit: int = 200) -> int:
    require_service_access(
        VERIFICATION_MAINTENANCE_WORKER,
        action="verification.cleanup_sessions",
    )
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
    require_service_access(
        VERIFICATION_MAINTENANCE_WORKER,
        action="verification.cleanup_media",
    )
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
        if _has_active_retention_hold(verification, now):
            record_audit_event(
                tenant=verification.tenant,
                action="retention.media_deletion_deferred",
                target_type="verification",
                target_id=verification.public_id,
                metadata={"reason": "legal_hold"},
            )
            continue
        retention_days = int(
            (verification.policy_snapshot_json or {}).get("media_retention_days", 30)
        )
        cutoff = verification.completed_at + timedelta(days=retention_days)
        if cutoff > now:
            continue

        media_deleted = False

        media_bucket = get_object_storage_media_bucket_name()
        for identity_document in verification.identity_documents.prefetch_related(
            "captures"
        ):
            for capture in identity_document.captures.filter(deleted_at__isnull=True):
                try:
                    if media_bucket:
                        delete_object(bucket_name=media_bucket, key=capture.storage_key)
                except Exception:
                    record_audit_event(
                        tenant=verification.tenant,
                        action="retention.media_deletion_failed",
                        target_type="verification",
                        target_id=verification.public_id,
                        metadata={"media_type": "document_capture"},
                    )
                    continue
                capture.status = DocumentCaptureStatus.DELETED
                capture.deleted_at = now
                capture.save(update_fields=["status", "deleted_at", "updated_at"])
                media_deleted = True

        for selfie in verification.selfie_captures.filter(deleted_at__isnull=True):
            try:
                if media_bucket:
                    delete_object(bucket_name=media_bucket, key=selfie.storage_key)
            except Exception:
                record_audit_event(
                    tenant=verification.tenant,
                    action="retention.media_deletion_failed",
                    target_type="verification",
                    target_id=verification.public_id,
                    metadata={"media_type": "selfie_capture"},
                )
                continue
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
