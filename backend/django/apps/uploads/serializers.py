from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.core.models import generate_public_id


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
            raise serializers.ValidationError({
                "mime_type": f"Unsupported MIME type for {purpose}."
            })

        if mime_type.startswith("image/") and file_size_bytes > 10 * 1024 * 1024:
            raise serializers.ValidationError({
                "file_size_bytes": "Image uploads must not exceed 10 MB."
            })

        if mime_type.startswith("video/") and file_size_bytes > 25 * 1024 * 1024:
            raise serializers.ValidationError({
                "file_size_bytes": "Video uploads must not exceed 25 MB."
            })

        return attrs

    def create(self, validated_data):
        upload_id = generate_public_id("upl")
        expires_at = timezone.now() + timedelta(minutes=10)
        upload_url = f"{settings.UPLOAD_URL_BASE.rstrip('/')}/{upload_id}"
        return {
            "upload_id": upload_id,
            "upload_url": upload_url,
            "expires_at": expires_at.isoformat(),
        }
