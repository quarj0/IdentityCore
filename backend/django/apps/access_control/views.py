from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access_control.models import Permission
from apps.access_control.serializers import serialize_permission, serialize_role
from common.permissions import IsTenantUser
from common.responses import success_response


class RoleListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        roles = request.user.tenant.roles.prefetch_related(
            "role_permissions__permission"
        ).order_by("name")
        return success_response(
            {"results": [serialize_role(role) for role in roles]},
            request=request,
        )


class PermissionListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        permissions = Permission.objects.order_by("code")
        return success_response(
            {
                "results": [
                    serialize_permission(permission) for permission in permissions
                ]
            },
            request=request,
        )
