from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class ProjectEnvironment(models.TextChoices):
    SANDBOX = "sandbox", "Sandbox"
    PRODUCTION = "production", "Production"


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class Project(PublicIdModel, BaseModel):
    public_id_prefix = "prj"
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="projects"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    environment = models.CharField(
        max_length=16,
        choices=ProjectEnvironment.choices,
        default=ProjectEnvironment.SANDBOX,
    )
    status = models.CharField(
        max_length=16,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
        db_index=True,
    )
    allowed_origins_json = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_projects",
    )

    class Meta:
        ordering = ["environment", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"], name="project_tenant_slug_uniq"
            )
        ]

    def clean(self):
        super().clean()
        if self.created_by_id and self.created_by.tenant_id != self.tenant_id:
            raise ValidationError(
                {"created_by": "Projects must be created by a user in the same tenant."}
            )

    @property
    def allowed_origins(self):
        return list(self.allowed_origins_json)

    def __str__(self):
        return f"{self.tenant.slug}/{self.slug}"
