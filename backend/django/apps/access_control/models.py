from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel, PublicIdModel, TimestampedModel


class RoleScope(models.TextChoices):
    PLATFORM = "platform", "Platform"
    TENANT = "tenant", "Tenant"


class RoleStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class Role(PublicIdModel, BaseModel):
    public_id_prefix = "rol"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="roles",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scope = models.CharField(max_length=32, choices=RoleScope.choices, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=RoleStatus.choices,
        default=RoleStatus.ACTIVE,
        db_index=True,
    )
    is_system_role = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="access_control_role_unique_tenant_name"),
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(tenant__isnull=True),
                name="access_control_role_unique_platform_name",
            ),
            models.CheckConstraint(
                condition=(
                    Q(scope=RoleScope.PLATFORM, tenant__isnull=True)
                    | Q(scope=RoleScope.TENANT, tenant__isnull=False)
                ),
                name="access_control_role_scope_matches_tenant",
            ),
        ]

    def clean(self):
        super().clean()
        if self.scope == RoleScope.PLATFORM and self.tenant_id is not None:
            raise ValidationError({"tenant": "Platform roles cannot belong to a tenant."})
        if self.scope == RoleScope.TENANT and self.tenant_id is None:
            raise ValidationError({"tenant": "Tenant roles must belong to a tenant."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Permission(TimestampedModel):
    code = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="access_control_role_permission_unique")
        ]


class UserRole(models.Model):
    user = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="user_roles",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role", "tenant"], name="access_control_user_role_unique")
        ]

    def clean(self):
        super().clean()
        if self.role.scope == RoleScope.PLATFORM:
            if self.tenant_id is not None:
                raise ValidationError({"tenant": "Platform role assignments cannot include a tenant."})
            if not self.user.is_platform_admin:
                raise ValidationError({"user": "Only platform admins can receive platform roles."})
        else:
            if self.tenant_id is None:
                raise ValidationError({"tenant": "Tenant role assignments must include a tenant."})
            if self.role.tenant_id != self.tenant_id:
                raise ValidationError({"tenant": "Assignment tenant must match the role tenant."})
            if self.user.tenant_id != self.tenant_id:
                raise ValidationError({"user": "Assignment tenant must match the user tenant."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
