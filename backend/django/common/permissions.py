from rest_framework.permissions import BasePermission

from common.authorization import (
    AuthorizationAction,
    decide_api_client_access,
    decide_user_access,
)


class IsTenantUser(BasePermission):
    message = "A tenant-scoped platform user is required."

    def has_permission(self, request, view):
        permission_code = getattr(view, "required_permission_code", None)
        return decide_user_access(
            request.user,
            action=AuthorizationAction.TENANT_ACCESS,
            permission_code=permission_code,
        ).allowed

    def has_object_permission(self, request, view, obj):
        permission_code = getattr(view, "required_permission_code", None)
        return decide_user_access(
            request.user,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=obj,
            permission_code=permission_code,
        ).allowed


class HasAPIClientScopes(BasePermission):
    required_scopes: tuple[str, ...] = ()
    message = "The API client does not have the required scope."

    def has_permission(self, request, view):
        required_scopes = getattr(view, "required_scopes", self.required_scopes)
        return decide_api_client_access(
            getattr(request, "api_client", None), required_scopes=required_scopes
        ).allowed

    def has_object_permission(self, request, view, obj):
        required_scopes = getattr(view, "required_scopes", self.required_scopes)
        return decide_api_client_access(
            getattr(request, "api_client", None),
            required_scopes=required_scopes,
            tenant=obj,
        ).allowed


class IsManualReviewUser(BasePermission):
    message = "A tenant reviewer or platform administrator is required."

    def has_permission(self, request, view):
        return decide_user_access(
            request.user, action=AuthorizationAction.MANUAL_REVIEW
        ).allowed
