from common.fields import environment_for_instance
import hashlib
import logging
from uuid import uuid4

from django.db import DatabaseError, transaction
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.uploads.serializers import UploadCreateSerializer
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.consent.services import lock_session_consent
from apps.uploads.scanning import inspect_upload_content
from apps.uploads.provenance import issue_receipt
from apps.uploads.original_cleanup import cleanup_original_upload
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


def _lock_upload_consent(request, purpose, action):
    scope = {
        UploadPurpose.DOCUMENT_CAPTURE: "document",
        UploadPurpose.SELFIE_CAPTURE: "biometrics",
        UploadPurpose.LIVENESS_CAPTURE: "biometrics",
    }.get(purpose)
    if scope is None:
        raise ValidationError("This upload purpose is unavailable.")
    return lock_session_consent(request, scope=scope, action=action)


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


_COMPLETED = {UploadStatus.UPLOADED, UploadStatus.CONSUMED, UploadStatus.PROMOTED}


def _locked_upload(request, upload_id):
    # Global audit -> case -> session -> upload order also used by withdrawal.
    upload = _upload_for_session(request, upload_id)
    proof = _lock_upload_consent(request, upload.purpose, "upload:transfer")
    upload = Upload.objects.select_for_update().get(pk=upload.pk)
    if upload.is_expired or upload.status == UploadStatus.EXPIRED:
        raise ValidationError({"file": "This upload has expired."})
    return upload, proof


def _admit_transfer(request, upload_id, operation_id):
    with transaction.atomic():
        upload, proof = _locked_upload(request, upload_id)
        record_audit_event(
            tenant=request.tenant,
            request=request,
            action="upload.transfer_admitted",
            target_type="upload",
            target_id=upload.public_id,
            metadata={
                "operation_id": operation_id,
                "consent_record_id": proof.public_id,
                "purpose": upload.purpose,
            },
        )
        return upload


def _delete_temporary_object(bucket_name, key, upload, operation_id):
    try:
        delete_object(bucket_name=bucket_name, key=key)
    except Exception as exc:
        logger.warning(
            "Temporary upload cleanup failed upload=%s operation=%s error=%s",
            upload.public_id,
            operation_id,
            type(exc).__name__,
        )


def _validate_state(upload, checksum):
    if upload.status in _COMPLETED:
        if upload.checksum_sha256 != checksum:
            raise ValidationError(
                {"file": "This upload was already completed with different content."}
            )
        return True
    if upload.status != UploadStatus.INITIATED:
        raise ValidationError({"file": "This upload is no longer available."})
    return False


def _finalize_upload(
    request,
    *,
    upload_id: str,
    content: bytes,
    content_type: str,
    operation_id: str,
    cleanup_original: bool = False,
) -> Upload:
    upload = _upload_for_session(request, upload_id)
    checksum_sha256, quarantine_reason = _validate_upload_content(
        upload=upload,
        content=content,
        content_type=content_type,
    )
    with transaction.atomic():
        upload, _ = _locked_upload(request, upload_id)
        if quarantine_reason:
            if upload.status == UploadStatus.INITIATED:
                upload.status = UploadStatus.QUARANTINED
                upload.checksum_sha256 = checksum_sha256
                upload.quarantine_reason = quarantine_reason
                upload.save(
                    update_fields=[
                        "status",
                        "checksum_sha256",
                        "quarantine_reason",
                        "updated_at",
                    ]
                )
        elif _validate_state(upload, checksum_sha256):
            return upload
    # Commit quarantine before returning the validation error.
    if quarantine_reason:
        raise ValidationError(
            {
                "file": "This file could not be safely validated.",
                "reason": quarantine_reason,
            }
        )

    original_storage_key = upload.storage_key
    # Each attempt owns its candidate: a losing concurrent request must never
    # remove the winner's object, even when both contain the same bytes.
    finalized_storage_key = f"{original_storage_key}.validated.{operation_id}"
    if len(finalized_storage_key) > Upload._meta.get_field("storage_key").max_length:
        raise ValidationError({"file": "This upload storage location is unavailable."})
    bucket_name = get_object_storage_temp_bucket_name()
    try:
        put_object_bytes(
            bucket_name=bucket_name,
            key=finalized_storage_key,
            tenant_scope=upload.tenant.public_id,
            environment=environment_for_instance(upload),
            content=content,
            content_type=upload.mime_type,
        )
    except Exception:
        _delete_temporary_object(
            bucket_name, finalized_storage_key, upload, operation_id
        )
        raise
    try:
        with transaction.atomic():
            locked, _ = _locked_upload(request, upload_id)
            if not _validate_state(locked, checksum_sha256):
                if cleanup_original:
                    locked.original_storage_key = original_storage_key
                locked.storage_key = finalized_storage_key
                locked.status = UploadStatus.UPLOADED
                locked.checksum_sha256 = checksum_sha256
                locked.quarantine_reason = ""
                locked.capture_provenance_version = 1
                locked.capture_receipt = issue_receipt(locked)
                locked.save(
                    update_fields=[
                        "storage_key",
                        "original_storage_key",
                        "status",
                        "checksum_sha256",
                        "quarantine_reason",
                        "capture_receipt",
                        "capture_provenance_version",
                        "updated_at",
                    ]
                )
    except DatabaseError:
        # A lost commit acknowledgement is ambiguous. Never delete an object
        # which the database may already have accepted. Lifecycle reconciles it.
        logger.warning(
            "Upload finalization uncertain upload=%s operation=%s",
            upload.public_id,
            operation_id,
        )
        raise
    except Exception:
        _delete_temporary_object(
            bucket_name, finalized_storage_key, upload, operation_id
        )
        raise
    if locked.storage_key != finalized_storage_key:
        _delete_temporary_object(
            bucket_name, finalized_storage_key, upload, operation_id
        )
    if cleanup_original and locked.storage_key == finalized_storage_key:
        cleanup_original_upload(locked, immediate=True)
    return locked


class UploadCreateView(APIView):
    authentication_classes = [VerificationSessionAuthentication]
    permission_classes = [IsAuthenticated]
    required_session_action = "upload:create"

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require_verification_session_action(request, self.required_session_action)

    @transaction.atomic
    def post(self, request):
        serializer = UploadCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        _lock_upload_consent(
            request, serializer.validated_data["purpose"], self.required_session_action
        )
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
        operation_id = uuid4().hex
        _admit_transfer(request, upload_id, operation_id)
        content = b"".join(uploaded_file.chunks())
        try:
            upload = _finalize_upload(
                request,
                upload_id=upload_id,
                content=content,
                content_type=uploaded_file.content_type,
                operation_id=operation_id,
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


class UploadCompleteView(UploadTransferView):
    def post(self, request, upload_id: str):
        operation_id = uuid4().hex
        upload = _admit_transfer(request, upload_id, operation_id)
        if upload.status in _COMPLETED:
            return success_response({"upload_id": upload.public_id}, request=request)
        try:
            content, content_type = get_object_bytes(
                bucket_name=get_object_storage_temp_bucket_name(),
                key=upload.storage_key,
                tenant_scope=upload.tenant.public_id,
                environment=environment_for_instance(upload),
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
                operation_id=operation_id,
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
