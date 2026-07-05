from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class NotificationRecipientType(models.TextChoices):
    PLATFORM_USER = "platform_user", "Platform User"
    VERIFICATION_SUBJECT = "verification_subject", "Verification Subject"


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    IN_APP = "in_app", "In-App"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Notification(PublicIdModel, BaseModel):
    public_id_prefix = "ntf"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="notifications",
    )
    recipient_type = models.CharField(
        max_length=32,
        choices=NotificationRecipientType.choices,
        db_index=True,
    )
    recipient = models.CharField(max_length=255)
    channel = models.CharField(
        max_length=32,
        choices=NotificationChannel.choices,
        db_index=True,
    )
    template_code = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=32,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        db_index=True,
    )
    subject = models.CharField(max_length=255, blank=True)
    body_preview = models.TextField(blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.status == NotificationStatus.SENT and self.sent_at is None:
            raise ValidationError({"sent_at": "Sent notifications must include a sent timestamp."})
        if self.status != NotificationStatus.SENT and self.sent_at is not None:
            raise ValidationError({"sent_at": "Only sent notifications may include a sent timestamp."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.public_id
