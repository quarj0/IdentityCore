import hashlib
import logging

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.uploads.serializers import UploadCreateSerializer
from apps.uploads.models import Upload, UploadStatus
from apps.uploads.scanning import inspect_upload_content
from common.authentication import (
    VerificationSessionAuthentication,
    require_verification_session_action,
)
from common.responses import error_response, success_response
from common.storage import (
    delete_object,
    get_object_bytes,
    get_object_storage_temp_bucket_name,
    put_object_bytes,
)

logger = logging.getLogger(__name__)


def _upload_for_session(request, upload_id: str) -> Upload:
    upload = Upload.objects.filter(
        public_id=upload_id,
        tenant=request.tenant,
        verification_session=request.verification_session,
        deleted_at__isnull=True,
    ).first()
    if upload is None:
        raise NotFound("This upload is no longer available.")
    return upload


def _validate_upload_content(
    *, upload: Upload, content: bytes, content_type: str
) -> tuple[str, str]:
    if len(content) != upload.file_size_bytes:
        raise ValidationError(
            {"file": "The selected file changed. Please choose it again."}
        )
    if content_type != upload.mime_type:
        raise ValidationError(
            {"file": "The selected file type does not match the upload."}
        )
    checksum_sha256 = hashlib.sha256(content).hexdigest()
    content_is_safe, quarantine_reason = inspect_upload_content(
        content=content,
        declared_mime_type=upload.mime_type,
    )
    return checksum_sha256, "" if content_is_safe else quarantine_reason


def _finalize_upload(
    request,
    *,
    upload_id: str,
    content: bytes,
    content_type: str,
    cleanup_original: bool = False,
) -> Upload:
    upload = _upload_for_session(request, upload_id)
    if upload.is_expired or upload.status == UploadStatus.EXPIRED:
        raise ValidationError({"file": "This upload has expired."})
    checksum_sha256, quarantine_reason = _validate_upload_content(
        upload=upload,
        content=content,
        content_type=content_type,
    )
    if quarantine_reason:
        with transaction.atomic():
            locked = Upload.objects.select_for_update().get(pk=upload.pk)
            if locked.status == UploadStatus.INITIATED:
                locked.status = UploadStatus.QUARANTINED
                locked.checksum_sha256 = checksum_sha256
                locked.quarantine_reason = quarantine_reason
                locked.save(
                    update_fields=[
                        "status",
                        "checksum_sha256",
                        "quarantine_reason",
                        "updated_at",
                    ]
                )
        raise ValidationError(
            {
                "file": "This file could not be safely validated.",
                "reason": quarantine_reason,
            }
        )

    if upload.status in {
        UploadStatus.UPLOADED,
        UploadStatus.CONSUMED,
        UploadStatus.PROMOTED,
    }:
        if upload.checksum_sha256 != checksum_sha256:
            raise ValidationError(
                {"file": "This upload was already completed with different content."}
            )
        return upload
    if upload.status != UploadStatus.INITIATED:
        raise ValidationError({"file": "This upload is no longer available."})

    original_storage_key = upload.storage_key
    finalized_storage_key = f"{original_storage_key}.validated.{checksum_sha256[:16]}"
    bucket_name = get_object_storage_temp_bucket_name()
    put_object_bytes(
        bucket_name=bucket_name,
        key=finalized_storage_key,
        content=content,
        content_type=upload.mime_type,
    )
    with transaction.atomic():
        locked = Upload.objects.select_for_update().get(pk=upload.pk)
        if locked.status == UploadStatus.INITIATED:
            locked.storage_key = finalized_storage_key
            locked.status = UploadStatus.UPLOADED
            locked.checksum_sha256 = checksum_sha256
            locked.quarantine_reason = ""
            locked.save(
                update_fields=[
                    "storage_key",
                    "status",
                    "checksum_sha256",
                    "quarantine_reason",
                    "updated_at",
                ]
            )
        elif locked.checksum_sha256 != checksum_sha256:
            raise ValidationError(
                {"file": "This upload was already completed with different content."}
            )
    if cleanup_original and original_storage_key != finalized_storage_key:
        try:
            delete_object(bucket_name=bucket_name, key=original_storage_key)
        except Exception as exc:
            logger.warning(
                "Validated upload %s but could not delete its original temporary object: %s",
                locked.public_id,
                exc,
            )
    return locked


class UploadCreateView(APIView):
    authentication_classes = [VerificationSessionAuthentication]
    permission_classes = [IsAuthenticated]
    required_session_action = "upload:create"

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require_verification_session_action(request, self.required_session_action)

    def post(self, request):
        serializer = UploadCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return success_response(
            payload, request=request, status=status.HTTP_201_CREATED
        )


class UploadTransferView(APIView):
    authentication_classes = [VerificationSessionAuthentication]
    permission_classes = [IsAuthenticated]
    required_session_action = "upload:transfer"

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require_verification_session_action(request, self.required_session_action)

    def post(self, request, upload_id: str):
        upload = _upload_for_session(request, upload_id)
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            raise ValidationError({"file": "Choose a file to upload."})
        if uploaded_file.size != upload.file_size_bytes:
            raise ValidationError(
                {"file": "The selected file changed. Please choose it again."}
            )
        content = b"".join(uploaded_file.chunks())
        try:
            upload = _finalize_upload(
                request,
                upload_id=upload_id,
                content=content,
                content_type=uploaded_file.content_type,
            )
        except ValidationError as exc:
            details = getattr(exc, "detail", {})
            if isinstance(details, dict) and "reason" in details:
                return error_response(
                    "upload_quarantined",
                    "This file could not be safely validated.",
                    details={"reason": str(details["reason"])},
                    request=request,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise
        return success_response({"upload_id": upload.public_id}, request=request)


class UploadCompleteView(UploadTransferView):
    def post(self, request, upload_id: str):
        upload = _upload_for_session(request, upload_id)
        if upload.status in {
            UploadStatus.UPLOADED,
            UploadStatus.CONSUMED,
            UploadStatus.PROMOTED,
        }:
            return success_response({"upload_id": upload.public_id}, request=request)
        try:
            content, content_type = get_object_bytes(
                bucket_name=get_object_storage_temp_bucket_name(),
                key=upload.storage_key,
                max_bytes=upload.file_size_bytes,
            )
        except ValueError as exc:
            raise ValidationError(
                {"file": "The uploaded object exceeds its declared size."}
            ) from exc
        try:
            upload = _finalize_upload(
                request,
                upload_id=upload_id,
                content=content,
                content_type=content_type,
                cleanup_original=True,
            )
        except ValidationError as exc:
            details = getattr(exc, "detail", {})
            if isinstance(details, dict) and "reason" in details:
                return error_response(
                    "upload_quarantined",
                    "This file could not be safely validated.",
                    details={"reason": str(details["reason"])},
                    request=request,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise
        return success_response({"upload_id": upload.public_id}, request=request)
