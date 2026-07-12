from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class IncidentStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In progress"
    RESOLVED = "resolved", "Resolved"


class IncidentSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class Incident(PublicIdModel, BaseModel):
    public_id_prefix = "inc"

    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=IncidentStatus.choices, db_index=True
    )
    severity = models.CharField(
        max_length=32, choices=IncidentSeverity.choices, db_index=True
    )
    owner_team = models.CharField(max_length=120, blank=True)
    affected_surface = models.CharField(max_length=120, blank=True)
    detected_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-detected_at"]
