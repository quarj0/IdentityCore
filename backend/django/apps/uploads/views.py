from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.uploads.serializers import UploadCreateSerializer
from apps.uploads.models import Upload, UploadStatus
from common.authentication import VerificationSessionAuthentication
from common.responses import success_response
from common.storage import get_object_storage_temp_bucket_name, put_object_bytes


class UploadCreateView(APIView):
    authentication_classes = [VerificationSessionAuthentication]
    permission_classes = [IsAuthenticated]

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

    def post(self, request, upload_id: str):
        upload = Upload.objects.filter(
            public_id=upload_id,
            tenant=request.tenant,
            verification_session=request.verification_session,
            status=UploadStatus.INITIATED,
            deleted_at__isnull=True,
        ).first()
        if upload is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("This upload is no longer available.")

        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "Choose a file to upload."})
        if uploaded_file.size != upload.file_size_bytes:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "The selected file changed. Please choose it again."})
        if uploaded_file.content_type != upload.mime_type:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"file": "The selected file type does not match the upload."})

        put_object_bytes(
            bucket_name=get_object_storage_temp_bucket_name(),
            key=upload.storage_key,
            content=uploaded_file.read(),
            content_type=upload.mime_type,
        )
        return success_response({"upload_id": upload.public_id}, request=request)
