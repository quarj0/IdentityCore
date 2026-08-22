import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import BaseModel, PublicIdModel, generate_public_id
from common.fields import EncryptedJSONField


class APIClientStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DISABLED = "disabled", "Disabled"
    ROTATING = "rotating", "Rotating"
    REVOKED = "revoked", "Revoked"


class APIClient(PublicIdModel, BaseModel):
    public_id_prefix = "api"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="api_clients",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="api_clients",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=64, unique=True, editable=False)
    client_secret_hash = models.CharField(max_length=255)
    previous_client_secret_hash = models.CharField(
        max_length=255, blank=True, default=""
    )
    previous_client_secret_expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=APIClientStatus.choices,
        default=APIClientStatus.ACTIVE,
        db_index=True,
    )
    scopes_json = models.JSONField(default=list, blank=True)
    allowed_ips_json = models.JSONField(default=list, blank=True)
    rate_limit_per_minute = models.PositiveIntegerField(default=60)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_api_clients",
    )
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def scopes(self) -> list[str]:
        return list(self.scopes_json)

    @property
    def allowed_ips(self) -> list[str]:
        return list(self.allowed_ips_json)

    def clean(self):
        super().clean()
        if self.created_by_id and self.created_by.tenant_id != self.tenant_id:
            raise ValidationError(
                {
                    "created_by": "API clients must be created by a user in the same tenant."
                }
            )
        if self.created_by_id and self.created_by.is_platform_admin:
            raise ValidationError(
                {
                    "created_by": "Platform admins must act through a tenant user context to create API clients."
                }
            )

    def save(self, *args, **kwargs):
        if not self.client_id:
            self.client_id = generate_public_id("cli")
        self.full_clean()
        return super().save(*args, **kwargs)

    def set_client_secret(self, raw_secret: str) -> None:
        self.client_secret_hash = make_password(raw_secret)

    def rotate_client_secret(self, raw_secret: str, *, overlap_expires_at) -> None:
        """Replace the secret while retaining its hash for a bounded overlap."""
        self.previous_client_secret_hash = self.client_secret_hash
        self.previous_client_secret_expires_at = overlap_expires_at
        self.set_client_secret(raw_secret)

    def verify_client_secret(self, raw_secret: str) -> bool:
        if check_password(raw_secret, self.client_secret_hash):
            return True
        if (
            self.previous_client_secret_hash
            and self.previous_client_secret_expires_at
            and self.previous_client_secret_expires_at > timezone.now()
        ):
            return check_password(raw_secret, self.previous_client_secret_hash)
        return False

    @classmethod
    def generate_client_secret(cls) -> str:
        return secrets.token_urlsafe(32)

    def __str__(self) -> str:
        return self.name


class APIIdempotencyRecord(BaseModel):
    """Stores a tenant-scoped mutating request for safe replay."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="idempotency_records",
    )

    api_client = models.ForeignKey(
        APIClient,
        on_delete=models.CASCADE,
        related_name="idempotency_records",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="idempotency_records",
        null=True,
        blank=True,
    )
    key = models.CharField(max_length=255)
    operation = models.CharField(max_length=255)
    request_hash = models.CharField(max_length=64)
    method = models.CharField(max_length=16)
    path = models.CharField(max_length=512)
    response_data_json = EncryptedJSONField(
        null=True,
        blank=True,
        encryption_purpose="api_clients.idempotency.response",
    )
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(api_client__isnull=False) & Q(user__isnull=True))
                    | (Q(api_client__isnull=True) & Q(user__isnull=False))
                ),
                name="idempotency_record_has_one_principal",
            ),
            models.UniqueConstraint(
                fields=["tenant", "api_client", "key"],
                condition=Q(api_client__isnull=False),
                name="unique_api_client_idempotency_key",
            ),
            models.UniqueConstraint(
                fields=["tenant", "user", "key"],
                condition=Q(user__isnull=False),
                name="unique_user_idempotency_key",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["api_client", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
