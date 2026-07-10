from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.uploads.services import build_signed_upload_url, create_upload


UPLOAD_PURPOSE_CHOICES = (
    ("document_capture", "Document Capture"),
    ("selfie_capture", "Selfie Capture"),
    ("liveness_capture", "Liveness Capture"),
)


ALLOWED_MIME_TYPES_BY_PURPOSE = {
    "document_capture": {
        "image/jpeg",
        "image/png",
        "image/webp",
    },
    "selfie_capture": {
        "image/jpeg",
        "image/png",
        "image/webp",
    },
    "liveness_capture": {
        "video/mp4",
        "video/quicktime",  # .mov
        "video/webm",
    },
}


class UploadCreateSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=UPLOAD_PURPOSE_CHOICES)
    mime_type = serializers.CharField(max_length=100)
    file_size_bytes = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        purpose = attrs["purpose"]
        mime_type = attrs["mime_type"]
        file_size_bytes = attrs["file_size_bytes"]

        allowed = ALLOWED_MIME_TYPES_BY_PURPOSE[purpose]

        if mime_type not in allowed:
            raise serializers.ValidationError(
                {"mime_type": f"Unsupported MIME type for {purpose}."}
            )

        if mime_type.startswith("image/") and file_size_bytes > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                {"file_size_bytes": "Image uploads must not exceed 10 MB."}
            )

        if mime_type.startswith("video/") and file_size_bytes > 25 * 1024 * 1024:
            raise serializers.ValidationError(
                {"file_size_bytes": "Video uploads must not exceed 25 MB."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        expires_at = timezone.now() + timedelta(
            minutes=int(getattr(settings, "UPLOAD_URL_EXPIRES_MINUTES", 10))
        )
        upload = create_upload(
            verification_session=request.verification_session,
            purpose=validated_data["purpose"],
            mime_type=validated_data["mime_type"],
            file_size_bytes=validated_data["file_size_bytes"],
            expires_at=expires_at,
        )
        upload_headers = {"Content-Type": upload.mime_type}
        if getattr(settings, "OBJECT_STORAGE_ENFORCE_SERVER_SIDE_ENCRYPTION", True):
            encryption = getattr(
                settings, "OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION", ""
            ).strip()
            if encryption:
                upload_headers["x-amz-server-side-encryption"] = encryption
        return {
            "upload_id": upload.public_id,
            "upload_url": build_signed_upload_url(upload=upload),
            "upload_headers": upload_headers,
            "upload_transfer_path": f"/uploads/{upload.public_id}/transfer",
            "expires_at": expires_at.isoformat(),
        }
