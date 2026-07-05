from django.conf import settings
from django.utils import timezone

from apps.uploads.models import Upload, UploadPurpose, UploadStatus


PURPOSE_STORAGE_PREFIX = {
    UploadPurpose.DOCUMENT_CAPTURE: "uploads/documents",
    UploadPurpose.SELFIE_CAPTURE: "uploads/selfies",
    UploadPurpose.LIVENESS_CAPTURE: "uploads/liveness",
}


def build_upload_storage_key(*, purpose: str, upload_id: str) -> str:
    return f"{PURPOSE_STORAGE_PREFIX[purpose]}/{upload_id}"


def build_signed_upload_url(*, upload: Upload) -> str:
    return f"{settings.UPLOAD_URL_BASE.rstrip('/')}/{upload.storage_key}"


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
        storage_provider="local",
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        status=UploadStatus.INITIATED,
        expires_at=expires_at,
    )
    upload.ensure_public_id()
    upload.storage_key = build_upload_storage_key(
        purpose=purpose, upload_id=upload.public_id
    )
    upload.save()
    return upload


def consume_upload(*, upload: Upload) -> Upload:
    now = timezone.now()
    upload.status = UploadStatus.CONSUMED
    upload.consumed_at = now
    upload.save(update_fields=["status", "consumed_at", "updated_at"])
    return upload
