from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.accounts.managers import PlatformUserManager
from apps.core.models import BaseModel, PublicIdModel


class PlatformUserStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    INVITED = "invited", "Invited"
    SUSPENDED = "suspended", "Suspended"
    LOCKED = "locked", "Locked"


class PlatformUser(PublicIdModel, BaseModel, AbstractBaseUser, PermissionsMixin):
    public_id_prefix = "usr"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="platform_users",
        null=True,
        blank=True,
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    status = models.CharField(
        max_length=32,
        choices=PlatformUserStatus.choices,
        default=PlatformUserStatus.INVITED,
        db_index=True,
    )
    is_platform_admin = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    notification_preferences_json = models.JSONField(default=dict, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)

    objects = PlatformUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]
        constraints = [
            models.CheckConstraint(
                condition=Q(is_platform_admin=True) | Q(tenant__isnull=False),
                name="accounts_user_requires_tenant_or_platform_admin",
            ),
        ]

    def clean(self):
        super().clean()
        self.email = type(self).objects.normalize_email(self.email)
        if not self.is_platform_admin and self.tenant is None:
            raise ValidationError(
                {"tenant": "Non-platform admin users must belong to a tenant."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.status == PlatformUserStatus.ACTIVE

    def __str__(self) -> str:
        return self.email


class EmailVerificationToken(PublicIdModel, BaseModel):
    public_id_prefix = "evt"

    user = models.ForeignKey(
        PlatformUser,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.used_at is not None and self.revoked_at is not None:
            raise ValidationError(
                {"used_at": "A verification token cannot be both used and revoked."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PasswordResetToken(PublicIdModel, BaseModel):
    public_id_prefix = "prt"

    user = models.ForeignKey(
        PlatformUser,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.used_at is not None and self.revoked_at is not None:
            raise ValidationError(
                {"used_at": "A password reset token cannot be both used and revoked."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ContactInquiryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    REVIEWED = "reviewed", "Reviewed"
    RESOLVED = "resolved", "Resolved"
    SPAM = "spam", "Spam"


class ContactInquiry(PublicIdModel, BaseModel):
    public_id_prefix = "inq"

    full_name = models.CharField(max_length=255)
    business_email = models.EmailField()
    organization_name = models.CharField(max_length=255, blank=True)
    interest = models.CharField(max_length=64, blank=True)
    message = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=ContactInquiryStatus.choices,
        default=ContactInquiryStatus.PENDING,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id


class TeamInvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class TeamInvitation(PublicIdModel, BaseModel):
    public_id_prefix = "inv"
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="team_invitations"
    )
    email = models.EmailField()
    role = models.ForeignKey(
        "access_control.Role", on_delete=models.PROTECT, related_name="team_invitations"
    )
    status = models.CharField(
        max_length=16,
        choices=TeamInvitationStatus.choices,
        default=TeamInvitationStatus.PENDING,
        db_index=True,
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        PlatformUser, on_delete=models.PROTECT, related_name="sent_team_invitations"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "email"],
                condition=Q(status="pending"),
                name="pending_invitation_tenant_email_uniq",
            )
        ]
