from django.core.exceptions import ValidationError
from graphql import GraphQLError
from strawberry.types import Info

from apps.access_control.models import Role, RoleScope
from apps.accounts.models import PlatformUser
from apps.reviewers.models import PlatformAdminInvitation


def require_tenant_user(info: Info):
    request = info.context["request"]
    user = request.user
    if not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required.")
    if (
        getattr(user, "is_platform_admin", False)
        or getattr(user, "tenant_id", None) is None
    ):
        raise GraphQLError("A tenant-scoped platform user is required.")
    return user


def require_authenticated_user(info: Info):
    request = info.context["request"]
    user = request.user
    if not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required.")
    return user


def require_platform_admin(info: Info):
    request = info.context["request"]
    user = request.user
    if not getattr(user, "is_authenticated", False):
        raise GraphQLError("Authentication required.")
    if not getattr(user, "is_platform_admin", False):
        raise GraphQLError("A platform administrator is required.")
    return user


def raise_graphql_validation_error(exc: ValidationError) -> None:
    messages = exc.messages if hasattr(exc, "messages") else [str(exc)]
    raise GraphQLError(" ".join(message for message in messages if message))


def ensure_platform_role(
    *, name: str, description: str = "", created_by: PlatformUser | None = None
) -> Role:
    role, _ = Role.objects.get_or_create(
        tenant=None,
        name=name,
        defaults={
            "description": description,
            "scope": RoleScope.PLATFORM,
            "status": "active",
            "is_system_role": False,
        },
    )
    if created_by is not None and role.description != description and description:
        role.description = description
        role.save(update_fields=["description", "updated_at"])
    return role


def user_has_platform_role(user: PlatformUser, role_names: set[str]) -> bool:
    return user.user_roles.filter(
        role__scope=RoleScope.PLATFORM, role__name__in=role_names
    ).exists()


def serialize_platform_admin_invitation(invitation: PlatformAdminInvitation) -> dict:
    return {
        "id": invitation.public_id,
        "email": invitation.email,
        "role_id": invitation.role.public_id,
        "role_name": invitation.role.name,
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat(),
        "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
        "invited_by_email": invitation.invited_by.email,
        "created_at": invitation.created_at.isoformat(),
        "updated_at": invitation.updated_at.isoformat(),
    }
