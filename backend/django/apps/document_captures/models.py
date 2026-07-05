from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class DocumentCaptureSide(models.TextChoices):
    FRONT = "front", "Front"
    BACK = "back", "Back"
    SINGLE = "single", "Single"
    MRZ = "mrz", "MRZ"
    OTHER = "other", "Other"


class DocumentCaptureStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    VALIDATED = "validated", "Validated"
    REJECTED = "rejected", "Rejected"
    DELETED = "deleted", "Deleted"


class DocumentCapture(PublicIdModel, BaseModel):
    public_id_prefix = "dcp"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="document_captures",
    )
    identity_document = models.ForeignKey(
        "identity_documents.IdentityDocument",
        on_delete=models.PROTECT,
        related_name="captures",
    )
    side = models.CharField(max_length=16, choices=DocumentCaptureSide.choices)
    storage_url = models.URLField(blank=True)
    storage_key = models.CharField(max_length=255)
    storage_provider = models.CharField(max_length=64, default="local")
    mime_type = models.CharField(max_length=100, default="image/jpeg")
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    quality_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=32,
        choices=DocumentCaptureStatus.choices,
        default=DocumentCaptureStatus.UPLOADED,
        db_index=True,
    )
    captured_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.public_id
