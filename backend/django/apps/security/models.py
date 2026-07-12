from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class SecurityCaseStatus(models.TextChoices):
    INVESTIGATING = "investigating", "Investigating"
    BLOCKED = "blocked", "Blocked"
    CONTAINED = "contained", "Contained"


class SecurityCaseSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class SecurityCase(PublicIdModel, BaseModel):
    public_id_prefix = "sec"

    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=SecurityCaseStatus.choices, db_index=True
    )
    severity = models.CharField(
        max_length=32, choices=SecurityCaseSeverity.choices, db_index=True
    )
    owner_team = models.CharField(max_length=120, blank=True)
    signal = models.CharField(max_length=255, blank=True)
    affected_surface = models.CharField(max_length=120, blank=True)
    detected_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-detected_at"]
