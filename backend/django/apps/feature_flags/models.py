from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class FeatureFlagStatus(models.TextChoices):
    ENABLED = "enabled", "Enabled"
    DISABLED = "disabled", "Disabled"


class FeatureFlag(PublicIdModel, BaseModel):
    public_id_prefix = "flg"

    key = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=FeatureFlagStatus.choices, db_index=True
    )
    rollout_percent = models.PositiveSmallIntegerField(default=0)
    audience = models.CharField(max_length=120, blank=True)
    owner_team = models.CharField(max_length=120, blank=True)
    channel = models.CharField(max_length=120, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_feature_flags",
    )

    class Meta:
        ordering = ["key"]
