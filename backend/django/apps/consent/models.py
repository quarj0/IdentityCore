from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class ConsentTemplateStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class ConsentTemplate(PublicIdModel, BaseModel):
    public_id_prefix = "ctm"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="consent_templates",
    )
    name = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    language = models.CharField(max_length=16, default="en")
    content = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=ConsentTemplateStatus.choices,
        default=ConsentTemplateStatus.DRAFT,
        db_index=True,
    )
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_consent_templates",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name", "-version", "language"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name", "version", "language"],
                name="consent_template_tenant_name_version_language_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class ConsentRecord(PublicIdModel, BaseModel):
    public_id_prefix = "con"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    verification_subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    consent_template = models.ForeignKey(
        ConsentTemplate,
        on_delete=models.PROTECT,
        related_name="consent_records",
        null=True,
        blank=True,
    )
    consent_text_snapshot = models.TextField()
    accepted = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-accepted_at"]

    def __str__(self) -> str:
        return self.public_id
