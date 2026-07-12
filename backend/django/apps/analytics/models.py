from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class AnalyticsStatus(models.TextChoices):
    LIVE = "live", "Live"
    WATCH = "watch", "Watch"
    DRAFT = "draft", "Draft"


class AnalyticsDashboard(PublicIdModel, BaseModel):
    public_id_prefix = "anl"

    code = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=AnalyticsStatus.choices, db_index=True
    )
    primary_metric = models.CharField(max_length=255)
    secondary_metric = models.CharField(max_length=255, blank=True)
    tertiary_metric = models.CharField(max_length=255, blank=True)
    time_window = models.CharField(max_length=64, default="30 days")
    owner_team = models.CharField(max_length=120, blank=True)
    config_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["title"]
