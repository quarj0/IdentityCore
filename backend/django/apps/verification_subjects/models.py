from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class VerificationSubject(PublicIdModel, BaseModel):
    public_id_prefix = "sub"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verification_subjects",
    )
    external_reference = models.CharField(max_length=255, blank=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone_number = models.CharField(max_length=32, blank=True, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    metadata_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="verification_subjects.metadata",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.full_name or self.public_id
