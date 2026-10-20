"""Explicit reviewer grants for tests that exercise authorized review workflows."""

from apps.access_control.models import Permission, Role, RolePermission, UserRole


def grant_review_permission(user):
    if user.tenant_id is None:
        raise ValueError("Tenant reviewer fixtures need a tenant.")
    permission, _ = Permission.objects.get_or_create(
        code="review_verification", defaults={"name": "Review verification cases"}
    )
    role, _ = Role.objects.get_or_create(
        tenant_id=user.tenant_id,
        name="Test verification reviewer",
        defaults={"scope": "tenant", "status": "active"},
    )
    RolePermission.objects.get_or_create(role=role, permission=permission)
    UserRole.objects.get_or_create(user=user, role=role, tenant_id=user.tenant_id)
    return role
