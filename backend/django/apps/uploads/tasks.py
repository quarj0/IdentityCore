from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.uploads.models import Upload, UploadStatus


@shared_task(queue="retention")
def cleanup_expired_uploads_task(limit: int = 200) -> int:
    now = timezone.now()
    uploads = list(
        Upload.objects.select_related("tenant")
        .filter(
            status=UploadStatus.INITIATED,
            deleted_at__isnull=True,
            expires_at__lte=now,
        )
        .order_by("expires_at")[:limit]
    )
    for upload in uploads:
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
