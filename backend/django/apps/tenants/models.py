from django.db import models, transaction

from apps.core.models import BaseModel, PublicIdModel
from apps.organizations.models import Organization
from common.fields import EncryptedJSONField


class TenantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    PENDING = "pending", "Pending"
    PENDING_REVIEW = "pending_review", "Pending review"
    CLOSED = "closed", "Closed"


class Tenant(PublicIdModel, BaseModel):
    public_id_prefix = "ten"

    organization = models.OneToOneField(
        Organization,
        on_delete=models.PROTECT,
        related_name="tenant",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    status = models.CharField(
        max_length=32,
        choices=TenantStatus.choices,
        default=TenantStatus.PENDING_REVIEW,
        db_index=True,
    )
    settings_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="tenants.settings",
    )

    class Meta:
        ordering = ["name"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        # The first settings envelope and owning tenant insert commit together.
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class TenantDataKey(PublicIdModel, BaseModel):
    """Only wrapped key material; scope exists before a tenant's first insert."""

    public_id_prefix = "tdk"
    tenant_scope = models.CharField(max_length=64)
    environment = models.CharField(
        max_length=16,
        choices=[
            ("sandbox", "Sandbox"),
            ("production", "Production"),
            ("shared", "Tenant administration"),
        ],
    )
    version = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    wrapping_provider = models.CharField(max_length=32, default="platform")
    wrapped_key_json = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_scope", "environment", "version"],
                name="tenant_data_key_unique_version",
            ),
            models.UniqueConstraint(
                fields=["tenant_scope", "environment"],
                condition=models.Q(active=True),
                name="tenant_data_key_unique_active",
            ),
        ]


class TenantKeyRotation(PublicIdModel, BaseModel):
    public_id_prefix = "tkr"
    tenant_scope = models.CharField(max_length=64)
    environment = models.CharField(
        max_length=16,
        choices=[
            ("sandbox", "Sandbox"),
            ("production", "Production"),
            ("shared", "Tenant administration"),
        ],
    )
    target_key = models.ForeignKey(TenantDataKey, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, default="pending")
    positions_json = models.JSONField(default=dict)
    migrated_count = models.PositiveIntegerField(default=0)
    conflict_count = models.PositiveIntegerField(default=0)
