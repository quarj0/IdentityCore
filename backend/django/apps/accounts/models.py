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
            raise ValidationError({"tenant": "Non-platform admin users must belong to a tenant."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.status == PlatformUserStatus.ACTIVE

    def __str__(self) -> str:
        return self.email
