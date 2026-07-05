from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class SelfieCaptureType(models.TextChoices):
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"


class SelfieCaptureStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    VALIDATED = "validated", "Validated"
    REJECTED = "rejected", "Rejected"
    DELETED = "deleted", "Deleted"


class SelfieCapture(PublicIdModel, BaseModel):
    public_id_prefix = "sel"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="selfie_captures",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="selfie_captures",
    )
    verification_subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="selfie_captures",
    )
    storage_url = models.URLField(blank=True)
    storage_key = models.CharField(max_length=255)
    storage_provider = models.CharField(max_length=64, default="local")
    capture_type = models.CharField(max_length=16, choices=SelfieCaptureType.choices)
    mime_type = models.CharField(max_length=100, default="image/jpeg")
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    face_count = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=32,
        choices=SelfieCaptureStatus.choices,
        default=SelfieCaptureStatus.UPLOADED,
        db_index=True,
    )
    captured_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.public_id
