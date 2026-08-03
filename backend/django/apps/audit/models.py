import json
import hashlib

from django.utils import timezone

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
    previous_event_hash = models.CharField(max_length=64, blank=True, editable=False)
    integrity_hash = models.CharField(max_length=64, blank=True, editable=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Audit events are append-only and may not be updated.")
        previous = (
            type(self).objects.filter(tenant_id=self.tenant_id)
            .order_by("-id")
            .first()
        )
        self.previous_event_hash = previous.integrity_hash if previous else ""
        payload = {
            "tenant_id": self.tenant_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "metadata_json": self.metadata_json,
            "sensitive_metadata_hash": self.sensitive_metadata_hash,
            "previous_event_hash": self.previous_event_hash,
            "created_at": self.created_at.isoformat(),
        }
        self.integrity_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit events are append-only and may not be deleted.")

    def __str__(self) -> str:
        return self.public_id
