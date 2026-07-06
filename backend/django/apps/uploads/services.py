from django.utils import timezone

from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from common.storage import (
    build_signed_upload_url as build_presigned_upload_url,
    determine_storage_provider,
    get_object_storage_media_bucket_name,
    get_object_storage_temp_bucket_name,
    move_object,
)

PURPOSE_STORAGE_SEGMENT = {
    UploadPurpose.DOCUMENT_CAPTURE: "documents",
    UploadPurpose.SELFIE_CAPTURE: "selfies",
    UploadPurpose.LIVENESS_CAPTURE: "liveness",
}


def build_upload_storage_key(*, verification, purpose: str, upload_id: str) -> str:
    return (
        f"organizations/{verification.organization.public_id}"
        f"/verifications/{verification.public_id}"
        f"/{PURPOSE_STORAGE_SEGMENT[purpose]}/{upload_id}"
    )


def build_signed_upload_url(*, upload: Upload) -> str:
    return build_presigned_upload_url(
        storage_key=upload.storage_key,
        mime_type=upload.mime_type,
        bucket_name=get_object_storage_temp_bucket_name(),
    )


def _move_upload_to_media_bucket(upload: Upload) -> None:
    source_bucket = get_object_storage_temp_bucket_name()
    destination_bucket = get_object_storage_media_bucket_name()
    if source_bucket and destination_bucket and source_bucket != destination_bucket:
        move_object(
            source_bucket=source_bucket,
            source_key=upload.storage_key,
            destination_bucket=destination_bucket,
        )


def create_upload(
    *,
    verification_session,
    purpose: str,
    mime_type: str,
    file_size_bytes: int,
    expires_at,
) -> Upload:
    verification = verification_session.verification
    upload = Upload(
        tenant=verification.tenant,
        verification=verification,
        verification_session=verification_session,
        purpose=purpose,
        storage_key="",
        storage_provider=determine_storage_provider(),
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        status=UploadStatus.INITIATED,
        expires_at=expires_at,
    )
    upload.ensure_public_id()
    upload.storage_key = build_upload_storage_key(
        verification=verification,
        purpose=purpose,
        upload_id=upload.public_id,
    )
    upload.save()
    return upload


def consume_upload(*, upload: Upload) -> Upload:
    now = timezone.now()
    upload.status = UploadStatus.CONSUMED
    upload.consumed_at = now
    upload.save(update_fields=["status", "consumed_at", "updated_at"])
    return upload


def promote_upload_to_media(*, upload: Upload) -> Upload:
    _move_upload_to_media_bucket(upload)
    if upload.status != UploadStatus.PROMOTED:
        upload.status = UploadStatus.PROMOTED
        upload.save(update_fields=["status", "updated_at"])
    return upload


def promote_upload_to_media_by_storage_key(storage_key: str) -> Upload | None:
    upload = Upload.objects.filter(storage_key=storage_key, deleted_at__isnull=True).first()
    if upload is None:
        return None
    return promote_upload_to_media(upload=upload)
