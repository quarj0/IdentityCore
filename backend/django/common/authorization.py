from dataclasses import dataclass
from enum import StrEnum


class AuthorizationAction(StrEnum):
    AUTHENTICATED = "authenticated"
    TENANT_ACCESS = "tenant.access"
    PLATFORM_ACCESS = "platform.access"
    MANUAL_REVIEW = "verification.manual_review"


class ReviewOwner(StrEnum):
    PLATFORM = "platform"
    TENANT = "tenant"


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class ServicePrincipal:
    name: str
    allowed_actions: frozenset[str]
    allow_cross_tenant: bool = False


def _allow() -> AuthorizationDecision:
    return AuthorizationDecision(allowed=True, reason="authorized")


def _deny(reason: str = "not_authorized") -> AuthorizationDecision:
    return AuthorizationDecision(allowed=False, reason=reason)


def _tenant_id(value):
    if hasattr(value, "tenant_id"):
        return value.tenant_id
    if hasattr(value, "pk"):
        return value.pk
    return value


def decide_user_access(
    user,
    *,
    action: AuthorizationAction,
    tenant=None,
    permission_code: str | None = None,
    review_owner: str | None = None,
) -> AuthorizationDecision:
    """Return the shared authorization decision for an interactive user.

    Supplying ``permission_code`` opts an action into explicit RBAC. Unknown,
    inactive, incorrectly scoped, and unassigned roles all deny by default.
    Existing tenant membership checks remain available for endpoints whose
    permissions have not yet been decomposed into role permission codes.
    """

    if not getattr(user, "is_authenticated", False):
        return _deny("authentication_required")

    if action == AuthorizationAction.AUTHENTICATED:
        return _allow()

    is_platform_admin = bool(getattr(user, "is_platform_admin", False))
    user_tenant_id = getattr(user, "tenant_id", None)
    target_tenant_id = _tenant_id(tenant) if tenant is not None else None

    # A supplied object without tenant ownership is not the same thing as a
    # collection-level authorization check. Fail closed for platform/global or
    # malformed objects passed to a tenant-scoped decision.
    if tenant is not None and target_tenant_id is None:
        return _deny("tenant_context_required")

    if action == AuthorizationAction.PLATFORM_ACCESS:
        return _allow() if is_platform_admin else _deny()

    if action == AuthorizationAction.MANUAL_REVIEW:
        if review_owner == ReviewOwner.PLATFORM:
            return _allow() if is_platform_admin else _deny()
        if review_owner == ReviewOwner.TENANT:
            if is_platform_admin or user_tenant_id is None:
                return _deny()
            if target_tenant_id is None or user_tenant_id != target_tenant_id:
                return _deny()
            return _has_role_permission(user, permission_code, target_tenant_id)

        # Collection-level permission; object ownership is enforced when the
        # queryset or object permission is evaluated.
        if is_platform_admin or user_tenant_id is not None:
            return _allow()
        return _deny()

    if action != AuthorizationAction.TENANT_ACCESS:
        return _deny("unknown_action")
    if is_platform_admin or user_tenant_id is None:
        return _deny()
    if target_tenant_id is not None and user_tenant_id != target_tenant_id:
        return _deny()
    return _has_role_permission(user, permission_code, user_tenant_id)


def _has_role_permission(
    user, permission_code: str | None, tenant_id
) -> AuthorizationDecision:
    if permission_code is None:
        return _allow()

    from apps.access_control.models import RoleScope, RoleStatus

    allowed = user.user_roles.filter(
        tenant_id=tenant_id,
        role__tenant_id=tenant_id,
        role__scope=RoleScope.TENANT,
        role__status=RoleStatus.ACTIVE,
        role__role_permissions__permission__code=permission_code,
    ).exists()
    return _allow() if allowed else _deny("permission_required")


def decide_api_client_access(
    api_client,
    *,
    required_scopes: tuple[str, ...] = (),
    tenant=None,
) -> AuthorizationDecision:
    if api_client is None or not getattr(api_client, "is_authenticated", False):
        return _deny("authentication_required")
    target_tenant_id = _tenant_id(tenant) if tenant is not None else None
    if tenant is not None and target_tenant_id is None:
        return _deny("tenant_context_required")
    if target_tenant_id is not None and api_client.tenant_id != target_tenant_id:
        return _deny()
    if not set(required_scopes).issubset(set(api_client.scopes)):
        return _deny("scope_required")
    return _allow()


def decide_service_access(
    principal: ServicePrincipal,
    *,
    action: str,
    resource=None,
) -> AuthorizationDecision:
    """Authorize an internal service against an explicitly allow-listed action.

    Requiring a tenant-owned resource prevents an unscoped worker operation from
    silently becoming a platform-wide capability.
    """

    if not principal.name or action not in principal.allowed_actions:
        return _deny("service_permission_required")
    if resource is None:
        return (
            _allow()
            if principal.allow_cross_tenant
            else _deny("tenant_context_required")
        )
    if getattr(resource, "tenant_id", None) is None:
        return _deny("tenant_context_required")
    return _allow()


def require_service_access(
    principal: ServicePrincipal,
    *,
    action: str,
    resource=None,
) -> None:
    from django.core.exceptions import PermissionDenied

    decision = decide_service_access(principal, action=action, resource=resource)
    if not decision.allowed:
        raise PermissionDenied("The service is not authorized for this operation.")
