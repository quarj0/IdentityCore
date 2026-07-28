from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class TemplateStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class TemplateCategory(models.TextChoices):
    GOVERNMENT_ID = "government_id", "Government ID"
    BANKING_KYC = "banking_kyc", "Banking KYC"
    EMPLOYMENT = "employment", "Employment"
    EDUCATION = "education", "Education"
    HEALTHCARE = "healthcare", "Healthcare"
    AGE_VERIFICATION = "age_verification", "Age Verification"


class Template(PublicIdModel, BaseModel):
    public_id_prefix = "tpl"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=64, choices=TemplateCategory.choices, db_index=True
    )
    status = models.CharField(
        max_length=32, choices=TemplateStatus.choices, db_index=True
    )
    version = models.CharField(max_length=32)
    slug = models.SlugField(max_length=255, blank=True, db_index=True)
    countries_json = models.JSONField(default=list, blank=True)
    required_checks_json = models.JSONField(default=list, blank=True)
    steps_json = models.JSONField(default=list, blank=True)
    settings_json = models.JSONField(default=dict, blank=True)
    provider_requirements_json = models.JSONField(default=list, blank=True)
    output_claims_json = models.JSONField(default=list, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    cloned_by_organizations = models.PositiveIntegerField(default=0)
    owner_team = models.CharField(max_length=120, blank=True)
    risk_level = models.CharField(max_length=32, blank=True)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_templates",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "version"],
                condition=~models.Q(slug=""),
                name="template_slug_version_uniq",
            )
        ]
