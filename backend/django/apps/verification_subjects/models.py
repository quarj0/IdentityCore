from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

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


class VerificationSubjectExport(PublicIdModel, BaseModel):
    public_id_prefix = "exp"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="subject_exports"
    )
    subject = models.ForeignKey(
        VerificationSubject, on_delete=models.PROTECT, related_name="exports"
    )
    payload_json = EncryptedJSONField(
        default=dict,
        encryption_purpose="verification_subjects.export_payload",
    )
    download_token_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField(db_index=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)

    def set_download_token(self, raw_token: str) -> None:
        self.download_token_hash = make_password(raw_token)

    def matches_download_token(self, raw_token: str) -> bool:
        return check_password(raw_token, self.download_token_hash)

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()
