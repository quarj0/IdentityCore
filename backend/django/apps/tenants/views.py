from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.tenants.serializers import serialize_tenant
from common.permissions import IsTenantUser
from common.responses import success_response


class TenantDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        return success_response(
            serialize_tenant(request.user.tenant),
            request=request,
        )
