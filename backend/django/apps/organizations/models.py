from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class OrganizationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    PENDING_REVIEW = "pending_review", "Pending review"
    CLOSED = "closed", "Closed"


class Organization(PublicIdModel, BaseModel):
    public_id_prefix = "org"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    industry = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=32,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.PENDING_REVIEW,
        db_index=True,
    )
    default_country_profile_id = models.CharField(max_length=64, blank=True)
    default_jurisdiction_id = models.CharField(max_length=64, blank=True)
    settings_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
