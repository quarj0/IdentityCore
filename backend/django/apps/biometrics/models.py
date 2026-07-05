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


class LivenessType(models.TextChoices):
    PASSIVE = "passive", "Passive"
    ACTIVE = "active", "Active"


class LivenessCheckStatus(models.TextChoices):
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"
    INCONCLUSIVE = "inconclusive", "Inconclusive"
    ERROR = "error", "Error"


class LivenessCheck(PublicIdModel, BaseModel):
    public_id_prefix = "liv"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="liveness_checks",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="liveness_checks",
    )
    selfie_capture = models.ForeignKey(
        SelfieCapture,
        on_delete=models.PROTECT,
        related_name="liveness_checks",
    )
    provider_check_id = models.CharField(max_length=64, blank=True)
    liveness_type = models.CharField(max_length=16, choices=LivenessType.choices)
    status = models.CharField(
        max_length=32,
        choices=LivenessCheckStatus.choices,
        default=LivenessCheckStatus.INCONCLUSIVE,
        db_index=True,
    )
    score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    confidence_level = models.CharField(max_length=32, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    model_version = models.CharField(max_length=64, blank=True)
    checked_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self) -> str:
        return self.public_id


class FaceMatchStatus(models.TextChoices):
    MATCHED = "matched", "Matched"
    NOT_MATCHED = "not_matched", "Not Matched"
    INCONCLUSIVE = "inconclusive", "Inconclusive"
    ERROR = "error", "Error"


class FaceMatch(PublicIdModel, BaseModel):
    public_id_prefix = "fmt"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="face_matches",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="face_matches",
    )
    selfie_capture = models.ForeignKey(
        SelfieCapture,
        on_delete=models.PROTECT,
        related_name="face_matches",
    )
    identity_document = models.ForeignKey(
        "identity_documents.IdentityDocument",
        on_delete=models.PROTECT,
        related_name="face_matches",
    )
    document_capture = models.ForeignKey(
        "document_captures.DocumentCapture",
        on_delete=models.PROTECT,
        related_name="face_matches",
        null=True,
        blank=True,
    )
    provider_check_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=32,
        choices=FaceMatchStatus.choices,
        default=FaceMatchStatus.INCONCLUSIVE,
        db_index=True,
    )
    match_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    confidence_level = models.CharField(max_length=32, blank=True)
    threshold_used = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    model_version = models.CharField(max_length=64, blank=True)
    matched_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-matched_at"]

    def __str__(self) -> str:
        return self.public_id
