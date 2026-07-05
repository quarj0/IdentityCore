import secrets
import hashlib

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class WebhookEndpointStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DISABLED = "disabled", "Disabled"
    FAILED = "failed", "Failed"


class WebhookEventStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


SUPPORTED_WEBHOOK_EVENTS = {
    "verification.created",
    "verification.consent_accepted",
    "verification.document_uploaded",
    "verification.selfie_uploaded",
    "verification.processing",
    "verification.manual_review_required",
    "verification.verified",
    "verification.rejected",
    "verification.expired",
    "verification.cancelled",
}


class WebhookEndpoint(PublicIdModel, BaseModel):
    public_id_prefix = "wh"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="webhook_endpoints",
    )
    url = models.URLField()
    description = models.CharField(max_length=255, blank=True)
    secret_hash = models.CharField(max_length=255)
    signing_key = models.CharField(max_length=64, blank=True)
    events_json = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=32,
        choices=WebhookEndpointStatus.choices,
        default=WebhookEndpointStatus.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_webhook_endpoints",
    )

    class Meta:
        ordering = ["url"]

    @property
    def events(self) -> list[str]:
        return list(self.events_json)

    def clean(self):
        super().clean()
        invalid_events = sorted(set(self.events) - SUPPORTED_WEBHOOK_EVENTS)
        if invalid_events:
            raise ValidationError({"events_json": f"Unsupported webhook events: {', '.join(invalid_events)}"})
        if self.created_by_id and self.created_by.tenant_id != self.tenant_id:
            raise ValidationError({"created_by": "Webhook endpoints must be created by a user in the same tenant."})

    def set_secret(self, raw_secret: str) -> None:
        self.secret_hash = make_password(raw_secret)
        self.signing_key = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    def verify_secret(self, raw_secret: str) -> bool:
        return check_password(raw_secret, self.secret_hash)

    @classmethod
    def generate_secret(cls) -> str:
        return secrets.token_urlsafe(32)

    def __str__(self) -> str:
        return self.url


class WebhookEvent(PublicIdModel, BaseModel):
    public_id_prefix = "evt"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="webhook_events",
    )
    webhook_endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.PROTECT,
        related_name="webhook_events",
    )
    event_type = models.CharField(max_length=120, db_index=True)
    payload_json = models.JSONField(default=dict)
    status = models.CharField(
        max_length=32,
        choices=WebhookEventStatus.choices,
        default=WebhookEventStatus.PENDING,
        db_index=True,
    )
    attempt_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id


class WebhookDeliveryAttempt(models.Model):
    webhook_event = models.ForeignKey(
        WebhookEvent,
        on_delete=models.CASCADE,
        related_name="delivery_attempts",
    )
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self) -> str:
        return f"{self.webhook_event.public_id}:{self.attempted_at.isoformat()}"
