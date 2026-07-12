import hashlib
import secrets

from django.core.exceptions import ValidationError
from django.db import models

from apps.access_control.models import RoleScope
from apps.core.models import BaseModel, PublicIdModel


class PlatformAdminInvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class PlatformAdminInvitation(PublicIdModel, BaseModel):
    public_id_prefix = "pinv"

    email = models.EmailField(db_index=True)
    role = models.ForeignKey(
        "access_control.Role",
        on_delete=models.PROTECT,
        related_name="platform_admin_invitations",
    )
    status = models.CharField(
        max_length=16,
        choices=PlatformAdminInvitationStatus.choices,
        default=PlatformAdminInvitationStatus.PENDING,
        db_index=True,
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="platform_admin_invitations_sent",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(status="pending"),
                name="platform_admin_pending_email_uniq",
            )
        ]

    def clean(self):
        super().clean()
        if self.role_id and self.role.scope != RoleScope.PLATFORM:
            raise ValidationError(
                {"role": "Platform admin invitations require a platform role."}
            )
        if self.invited_by_id and not self.invited_by.is_platform_admin:
            raise ValidationError(
                {"invited_by": "Only platform admins can invite other platform admins."}
            )

    @classmethod
    def generate_token(cls) -> str:
        return secrets.token_urlsafe(32)

    @classmethod
    def digest_token(cls, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def set_token(self, raw_token: str) -> None:
        self.token_hash = self.digest_token(raw_token)

    def __str__(self) -> str:
        return self.email
