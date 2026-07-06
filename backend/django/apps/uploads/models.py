from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel, PublicIdModel


class UploadPurpose(models.TextChoices):
    DOCUMENT_CAPTURE = "document_capture", "Document Capture"
    SELFIE_CAPTURE = "selfie_capture", "Selfie Capture"
    LIVENESS_CAPTURE = "liveness_capture", "Liveness Capture"


class UploadStatus(models.TextChoices):
    INITIATED = "initiated", "Initiated"
    CONSUMED = "consumed", "Consumed"
    PROMOTED = "promoted", "Promoted"
    EXPIRED = "expired", "Expired"
    DELETED = "deleted", "Deleted"


class Upload(PublicIdModel, BaseModel):
    public_id_prefix = "upl"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="uploads",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="uploads",
    )
    verification_session = models.ForeignKey(
        "verifications.VerificationSession",
        on_delete=models.PROTECT,
        related_name="uploads",
    )
    purpose = models.CharField(
        max_length=32,
        choices=UploadPurpose.choices,
        db_index=True,
    )
    storage_key = models.CharField(max_length=255, unique=True)
    storage_provider = models.CharField(max_length=64, default="local")
    mime_type = models.CharField(max_length=100)
    file_size_bytes = models.PositiveBigIntegerField()
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=32,
        choices=UploadStatus.choices,
        default=UploadStatus.INITIATED,
        db_index=True,
    )
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.verification_id and self.verification.tenant_id != self.tenant_id:
            raise ValidationError(
                {"verification": "Upload verification must belong to the same tenant."}
            )
        if (
            self.verification_session_id
            and self.verification_session.tenant_id != self.tenant_id
        ):
            raise ValidationError(
                {
                    "verification_session": "Upload session must belong to the same tenant."
                }
            )
        if (
            self.verification_id
            and self.verification_session_id
            and self.verification_session.verification_id != self.verification_id
        ):
            raise ValidationError(
                {
                    "verification_session": "Upload session must belong to the same verification."
                }
            )
        if self.status in {UploadStatus.CONSUMED, UploadStatus.PROMOTED} and self.consumed_at is None:
            raise ValidationError(
                {"consumed_at": "Consumed or promoted uploads must record when they were used."}
            )
        if self.status not in {UploadStatus.CONSUMED, UploadStatus.PROMOTED} and self.consumed_at is not None:
            raise ValidationError(
                {"consumed_at": "Only consumed or promoted uploads may include consumed_at."}
            )

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    def __str__(self) -> str:
        return self.public_id
