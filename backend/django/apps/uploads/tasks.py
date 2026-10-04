from datetime import timedelta

from celery import shared_task
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.uploads.models import Upload, UploadStatus
from apps.verifications.retention import (
    active_retention_holds,
    has_active_retention_hold,
)
from common.storage import (
    delete_object,
    get_object_storage_temp_bucket_name,
)
from common.authorization import ServicePrincipal, require_service_access

UPLOAD_RETENTION_WORKER = ServicePrincipal(
    name="upload-retention-worker",
    allowed_actions=frozenset({"upload.cleanup"}),
    allow_cross_tenant=True,
)

UPLOAD_DELETION_MAX_BACKOFF_HOURS = 24


def _defer_failed_deletion(upload: Upload, *, now, reason: str) -> None:
    upload.deletion_attempt_count += 1
    backoff_hours = min(
        2 ** max(upload.deletion_attempt_count - 1, 0),
        UPLOAD_DELETION_MAX_BACKOFF_HOURS,
    )
    upload.deletion_retry_at = now + timedelta(hours=backoff_hours)
    upload.save(
        update_fields=["deletion_attempt_count", "deletion_retry_at", "updated_at"]
    )
    record_audit_event(
        tenant=upload.tenant,
        action="retention.temporary_upload_deletion_failed",
        target_type="upload",
        target_id=upload.public_id,
        metadata={
            "reason": reason,
            "attempt_count": upload.deletion_attempt_count,
            "retry_at": upload.deletion_retry_at.isoformat(),
        },
    )


@shared_task(queue="retention")
def cleanup_expired_uploads_task(limit: int = 200) -> int:
    require_service_access(UPLOAD_RETENTION_WORKER, action="upload.cleanup")
    now = timezone.now()
    eligible = (
        Upload.objects.select_related("tenant")
        .annotate(
            held=Exists(
                active_retention_holds(now)
                .filter(tenant_id=OuterRef("tenant_id"))
                .filter(
                    Q(verification_id__isnull=True)
                    | Q(verification_id=OuterRef("verification_id"))
                )
            )
        )
        .filter(held=False)
        .filter(Q(deletion_retry_at__isnull=True) | Q(deletion_retry_at__lte=now))
    )
    initiated_uploads = list(
        eligible.filter(
            status__in=[
                UploadStatus.INITIATED,
                UploadStatus.UPLOADED,
                UploadStatus.QUARANTINED,
            ],
            deleted_at__isnull=True,
            expires_at__lte=now,
        ).order_by("expires_at")[:limit]
    )
    remaining = max(limit - len(initiated_uploads), 0)
    consumed_uploads = []
    if remaining:
        consumed_uploads = list(
            eligible.filter(
                status=UploadStatus.CONSUMED,
                deleted_at__isnull=True,
                consumed_at__lte=now - timedelta(hours=24),
            ).order_by("consumed_at")[:remaining]
        )
    uploads = initiated_uploads + consumed_uploads
    temp_bucket = get_object_storage_temp_bucket_name()
    cleaned = 0
    for upload in uploads:
        if has_active_retention_hold(
            tenant_id=upload.tenant_id,
            verification_id=upload.verification_id,
            now=timezone.now(),
        ):
            continue
        if not temp_bucket and upload.storage_provider != "local":
            _defer_failed_deletion(upload, now=now, reason="storage_not_configured")
            continue
        if temp_bucket:
            try:
                delete_object(bucket_name=temp_bucket, key=upload.storage_key)
            except Exception:
                _defer_failed_deletion(upload, now=now, reason="storage_delete_failed")
                continue
        upload.status = UploadStatus.EXPIRED
        upload.deleted_at = now
        upload.deletion_retry_at = None
        upload.save(
            update_fields=["status", "deleted_at", "deletion_retry_at", "updated_at"]
        )
        record_audit_event(
            tenant=upload.tenant,
            action="retention.temporary_upload_deleted",
            target_type="upload",
            target_id=upload.public_id,
            metadata={"purpose": upload.purpose},
        )
        cleaned += 1
    return cleaned
