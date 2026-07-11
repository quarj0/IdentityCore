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
        api_clients = request.user.tenant.api_clients.select_related("tenant").order_by(
            "name"
        )
        return success_response(
            {
                "results": [
                    serialize_api_client(api_client) for api_client in api_clients
                ]
            },
            request=request,
        )

    def post(self, request):
        serializer = APIClientCreateSerializer(
            data=request.data, context={"request": request}
        )
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
            serialize_api_client(
                api_client, include_secret=api_client._raw_client_secret
            ),
            request=request,
            status=status.HTTP_201_CREATED,
        )


class APIClientDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def obj(self, request, client_id):
        return request.user.tenant.api_clients.get(public_id=client_id)

    def get(self, request, client_id):
        return success_response(
            serialize_api_client(self.obj(request, client_id)), request=request
        )

    def patch(self, request, client_id):
        client = self.obj(request, client_id)
        for field in ("name", "rate_limit_per_minute"):
            if field in request.data:
                setattr(client, field, request.data[field])
        if "scopes" in request.data:
            client.scopes_json = request.data["scopes"]
        if "allowed_networks" in request.data:
            client.allowed_ips_json = request.data["allowed_networks"]
        client.save()
        return success_response(serialize_api_client(client), request=request)


class APIClientActionView(APIClientDetailView):
    def post(self, request, client_id, action):
        client = self.obj(request, client_id)
        secret = None
        if action == "rotate":
            secret = client.generate_client_secret()
            client.set_client_secret(secret)
            client.status = "active"
        elif action == "revoke":
            client.status = "revoked"
        elif action == "reactivate":
            client.status = "active"
        else:
            return success_response(
                {"detail": "Unsupported action."}, request=request, status=400
            )
        client.save()
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action=f"api_client.{action}",
            target_type="api_client",
            target_id=client.public_id,
        )
        return success_response(
            (
                serialize_api_client(client, include_secret=secret)
                if secret
                else serialize_api_client(client)
            ),
            request=request,
        )
