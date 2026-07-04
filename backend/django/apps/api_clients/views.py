from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.api_clients.serializers import APIClientCreateSerializer, serialize_api_client
from common.permissions import IsTenantUser
from common.responses import success_response


class APIClientListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        api_clients = (
            request.user.tenant.api_clients.select_related("tenant")
            .order_by("name")
        )
        return success_response(
            {"results": [serialize_api_client(api_client) for api_client in api_clients]},
            request=request,
        )

    def post(self, request):
        serializer = APIClientCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        api_client = serializer.save()
        return success_response(
            serialize_api_client(api_client, include_secret=api_client._raw_client_secret),
            request=request,
            status=status.HTTP_201_CREATED,
        )
