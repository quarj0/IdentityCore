from rest_framework.permissions import BasePermission


class IsTenantUser(BasePermission):
    message = "A tenant-scoped platform user is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and not getattr(user, "is_platform_admin", False)
            and getattr(user, "tenant_id", None) is not None
        )


class HasAPIClientScopes(BasePermission):
    required_scopes: tuple[str, ...] = ()
    message = "The API client does not have the required scope."

    def has_permission(self, request, view):
        api_client = getattr(request, "api_client", None)
        if api_client is None:
            return False

        required_scopes = getattr(view, "required_scopes", self.required_scopes)
        return set(required_scopes).issubset(set(api_client.scopes))
