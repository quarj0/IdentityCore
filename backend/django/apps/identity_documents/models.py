from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class IdentityDocumentStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    PROCESSING = "processing", "Processing"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"
    REJECTED = "rejected", "Rejected"


class IdentityDocument(PublicIdModel, BaseModel):
    public_id_prefix = "doc"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="identity_documents",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="identity_documents",
    )
    verification_subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="identity_documents",
    )
    document_type_id = models.CharField(max_length=64, db_index=True)
    country_profile_id = models.CharField(max_length=64, blank=True)
    local_document_name = models.CharField(max_length=255, blank=True)
    document_number_hash = models.CharField(max_length=255, blank=True, db_index=True)
    issuing_authority = models.CharField(max_length=255, blank=True)
    issued_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=IdentityDocumentStatus.choices,
        default=IdentityDocumentStatus.SUBMITTED,
        db_index=True,
    )
    extracted_data_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="identity_documents.extracted_data",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id
