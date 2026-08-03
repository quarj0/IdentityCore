import hashlib

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.uploads.serializers import UploadCreateSerializer
from apps.uploads.models import Upload, UploadStatus
from common.authentication import (
    VerificationSessionAuthentication,
    require_verification_session_action,
)
from common.responses import success_response
from common.storage import get_object_storage_temp_bucket_name, put_object_bytes


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

    @transaction.atomic
    def post(self, request, upload_id: str):
        upload = (
            Upload.objects.select_for_update()
            .filter(
                public_id=upload_id,
                tenant=request.tenant,
                verification_session=request.verification_session,
                status__in=[UploadStatus.INITIATED, UploadStatus.UPLOADED],
                deleted_at__isnull=True,
            )
            .first()
        )
        if upload is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("This upload is no longer available.")

        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "Choose a file to upload."})
        if upload.is_expired or upload.status == UploadStatus.EXPIRED:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "This upload has expired."})

        content = uploaded_file.read()
        checksum_sha256 = hashlib.sha256(content).hexdigest()
        if len(content) != upload.file_size_bytes:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "The selected file changed. Please choose it again."})
        if uploaded_file.content_type != upload.mime_type:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "The selected file type does not match the upload."})

        if upload.status == UploadStatus.UPLOADED:
            if upload.checksum_sha256 != checksum_sha256:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"file": "This upload was already completed with different content."})
            return success_response({"upload_id": upload.public_id}, request=request)

        put_object_bytes(
            bucket_name=get_object_storage_temp_bucket_name(),
            key=upload.storage_key,
            content=content,
            content_type=upload.mime_type,
        )
        upload.status = UploadStatus.UPLOADED
        upload.checksum_sha256 = checksum_sha256
        upload.save(update_fields=["status", "checksum_sha256", "updated_at"])
        return success_response({"upload_id": upload.public_id}, request=request)
