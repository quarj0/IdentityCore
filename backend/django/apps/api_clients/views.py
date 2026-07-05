from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
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
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="api_client.created",
            target_type="api_client",
            target_id=api_client.public_id,
            metadata={"client_id": api_client.client_id, "name": api_client.name},
        )
        return success_response(
            serialize_api_client(api_client, include_secret=api_client._raw_client_secret),
            request=request,
            status=status.HTTP_201_CREATED,
        )
