import json

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import PublicIdModel


class AuditActorType(models.TextChoices):
    PLATFORM_USER = "platform_user", "Platform User"
    API_CLIENT = "api_client", "API Client"
    VERIFICATION_SUBJECT = "verification_subject", "Verification Subject"
    SYSTEM = "system", "System"
    PROVIDER = "provider", "Provider"


class AuditEvent(PublicIdModel):
    public_id_prefix = "aud"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="audit_events",
    )
    actor_type = models.CharField(max_length=32, choices=AuditActorType.choices, db_index=True)
    actor_id = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=120, db_index=True)
    target_type = models.CharField(max_length=64, db_index=True)
    target_id = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    sensitive_metadata_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Audit events are append-only and may not be updated.")
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.public_id
