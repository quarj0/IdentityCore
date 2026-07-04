from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from apps.organizations.models import Organization


class TenantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
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
    settings_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
