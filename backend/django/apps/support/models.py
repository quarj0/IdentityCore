from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class SupportTicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In progress"
    RESOLVED = "resolved", "Resolved"


class SupportTicketPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class SupportTicket(PublicIdModel, BaseModel):
    public_id_prefix = "tkt"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="support_tickets",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=SupportTicketStatus.choices, db_index=True
    )
    priority = models.CharField(
        max_length=32, choices=SupportTicketPriority.choices, db_index=True
    )
    owner_team = models.CharField(max_length=120, blank=True)
    issue_type = models.CharField(max_length=120, blank=True)
    requester_email = models.EmailField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-updated_at"]
