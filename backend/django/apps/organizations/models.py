from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class OrganizationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    PENDING_EMAIL_VERIFICATION = (
        "pending_email_verification",
        "Pending email verification",
    )
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
    settings_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="organizations.settings",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class OrganizationSupportingDocument(PublicIdModel, BaseModel):
    public_id_prefix = "odoc"
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="supporting_documents")
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="organization_supporting_documents")
    uploaded_by = models.ForeignKey("accounts.PlatformUser", on_delete=models.PROTECT, related_name="organization_documents_uploaded")
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, default="application/pdf")
    file_size_bytes = models.PositiveBigIntegerField()
    storage_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=32, default="initiated", db_index=True)

    class Meta:
        ordering = ["created_at"]
