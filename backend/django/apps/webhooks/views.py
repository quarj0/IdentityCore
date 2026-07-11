from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.webhooks.serializers import (
    WebhookEndpointCreateSerializer,
    WebhookTestSerializer,
    serialize_webhook_endpoint,
)
from common.permissions import IsTenantUser
from common.responses import success_response
from apps.webhooks.models import WebhookEndpoint


class WebhookEndpointListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        endpoints = request.user.tenant.webhook_endpoints.order_by("url")
        return success_response(
            {
                "results": [
                    serialize_webhook_endpoint(endpoint) for endpoint in endpoints
                ]
            },
            request=request,
        )

    def post(self, request):
        serializer = WebhookEndpointCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        endpoint = serializer.save()
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="webhook_endpoint.created",
            target_type="webhook_endpoint",
            target_id=endpoint.public_id,
            metadata={"url": endpoint.url, "events": endpoint.events},
        )
        return success_response(
            {
                "id": endpoint.public_id,
                "secret": endpoint._raw_secret,
                "status": endpoint.status,
            },
            request=request,
            status=status.HTTP_201_CREATED,
        )


class WebhookEndpointTestView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def post(self, request, webhook_id: str):
        endpoint = get_object_or_404(
            WebhookEndpoint,
            tenant=request.user.tenant,
            public_id=webhook_id,
        )
        serializer = WebhookTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(endpoint=endpoint)
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="webhook.test_queued",
            target_type="webhook_endpoint",
            target_id=endpoint.public_id,
            metadata={"webhook_id": endpoint.public_id},
        )
        return success_response(
            {"queued": True}, request=request, status=status.HTTP_200_OK
        )


class WebhookEndpointDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def obj(self, request, webhook_id):
        return get_object_or_404(
            WebhookEndpoint, tenant=request.user.tenant, public_id=webhook_id
        )

    def get(self, request, webhook_id):
        return success_response(
            serialize_webhook_endpoint(self.obj(request, webhook_id)), request=request
        )

    def patch(self, request, webhook_id):
        endpoint = self.obj(request, webhook_id)
        for field in ("url", "description"):
            if field in request.data:
                setattr(endpoint, field, request.data[field])
        if "events" in request.data:
            endpoint.events_json = request.data["events"]
        endpoint.save()
        return success_response(serialize_webhook_endpoint(endpoint), request=request)


class WebhookEndpointActionView(WebhookEndpointDetailView):
    def post(self, request, webhook_id, action):
        endpoint = self.obj(request, webhook_id)
        if action == "disable":
            endpoint.status = "disabled"
        elif action == "reactivate":
            endpoint.status = "active"
        else:
            return success_response(
                {"detail": "Unsupported action."}, request=request, status=400
            )
        endpoint.save(update_fields=["status", "updated_at"])
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action=f"webhook_endpoint.{action}",
            target_type="webhook_endpoint",
            target_id=endpoint.public_id,
        )
        return success_response(serialize_webhook_endpoint(endpoint), request=request)
