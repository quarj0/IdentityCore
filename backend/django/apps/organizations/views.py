from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.organizations.serializers import serialize_organization
from common.permissions import IsTenantUser
from common.responses import success_response


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        return success_response(
            serialize_organization(request.user.tenant.organization),
            request=request,
        )
