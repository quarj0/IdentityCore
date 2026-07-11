from django.db import models
from apps.core.models import BaseModel, PublicIdModel


class WorkflowStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class Workflow(PublicIdModel, BaseModel):
    public_id_prefix = "wfl"
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="workflows"
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="workflows"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True,
    )
    steps_json = models.JSONField(default=list)
    settings_json = models.JSONField(default=dict)
    current_version = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_workflows",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="workflow_project_name_uniq"
            )
        ]


class WorkflowVersion(PublicIdModel):
    public_id_prefix = "wfv"
    workflow = models.ForeignKey(
        Workflow, on_delete=models.PROTECT, related_name="versions"
    )
    version = models.PositiveIntegerField()
    steps_json = models.JSONField(default=list)
    settings_json = models.JSONField(default=dict)
    policy = models.OneToOneField(
        "verification_policies.VerificationPolicy",
        on_delete=models.PROTECT,
        related_name="workflow_version",
    )
    published_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="published_workflow_versions",
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "version"], name="workflow_version_uniq"
            )
        ]
