import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel, generate_public_id


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

    def verify_client_secret(self, raw_secret: str) -> bool:
        return check_password(raw_secret, self.client_secret_hash)

    @classmethod
    def generate_client_secret(cls) -> str:
        return secrets.token_urlsafe(32)

    def __str__(self) -> str:
        return self.name
