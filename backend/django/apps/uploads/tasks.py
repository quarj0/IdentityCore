from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.uploads.models import Upload, UploadStatus
from common.storage import (
    delete_object,
    get_object_storage_temp_bucket_name,
)


@shared_task(queue="retention")
def cleanup_expired_uploads_task(limit: int = 200) -> int:
    now = timezone.now()
    initiated_uploads = list(
        Upload.objects.select_related("tenant")
        .filter(
            status=UploadStatus.INITIATED,
            deleted_at__isnull=True,
            expires_at__lte=now,
        )
        .order_by("expires_at")[:limit]
    )
    remaining = max(limit - len(initiated_uploads), 0)
    consumed_uploads = []
    if remaining:
        consumed_uploads = list(
            Upload.objects.select_related("tenant")
            .filter(
                status=UploadStatus.CONSUMED,
                deleted_at__isnull=True,
                consumed_at__lte=now - timedelta(hours=24),
            )
            .order_by("consumed_at")[:remaining]
        )
    uploads = initiated_uploads + consumed_uploads
    temp_bucket = get_object_storage_temp_bucket_name()
    for upload in uploads:
        if temp_bucket:
            try:
                delete_object(bucket_name=temp_bucket, key=upload.storage_key)
            except Exception:
                pass
        upload.status = UploadStatus.EXPIRED
        upload.deleted_at = now
        upload.save(update_fields=["status", "deleted_at", "updated_at"])
        record_audit_event(
            tenant=upload.tenant,
            action="retention.temporary_upload_deleted",
            target_type="upload",
            target_id=upload.public_id,
            metadata={"purpose": upload.purpose, "storage_key": upload.storage_key},
        )
    return len(uploads)
