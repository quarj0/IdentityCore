from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from common.permissions import IsTenantUser
from common.responses import success_response
from apps.api_clients.usage import usage_for_tenant


class APIUsageView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        response = success_response(
            {"results": usage_for_tenant(request.user.tenant)}, request=request
        )
        response["Cache-Control"] = "no-store"
        return response
