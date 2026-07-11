from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class VerificationPolicyStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class VerificationPolicy(PublicIdModel, BaseModel):
    public_id_prefix = "pol"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verification_policies",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="verification_policies",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=32,
        choices=VerificationPolicyStatus.choices,
        default=VerificationPolicyStatus.DRAFT,
        db_index=True,
    )
    required_document_types_json = models.JSONField(default=list, blank=True)
    required_liveness_level = models.CharField(max_length=32, default="passive")
    face_match_threshold = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.8500
    )
    manual_review_threshold = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.6500
    )
    verification_expiry_minutes = models.PositiveIntegerField(default=1440)
    media_retention_days = models.PositiveIntegerField(default=30)
    metadata_retention_days = models.PositiveIntegerField(default=365)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_verification_policies",
    )

    class Meta:
        ordering = ["name", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name", "version"],
                name="verification_policy_tenant_name_version_uniq",
            )
        ]

    def clean(self):
        super().clean()
        if self.created_by_id and self.created_by.tenant_id != self.tenant_id:
            raise ValidationError(
                {
                    "created_by": "Verification policies must be created by a user in the same tenant."
                }
            )

    @property
    def required_document_types(self) -> list[str]:
        return list(self.required_document_types_json)

    def snapshot(self) -> dict:
        return {
            "id": self.public_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status,
            "required_document_types": self.required_document_types,
            "required_liveness_level": self.required_liveness_level,
            "face_match_threshold": float(self.face_match_threshold),
            "manual_review_threshold": float(self.manual_review_threshold),
            "verification_expiry_minutes": self.verification_expiry_minutes,
            "media_retention_days": self.media_retention_days,
            "metadata_retention_days": self.metadata_retention_days,
        }

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
