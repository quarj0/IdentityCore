from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.api_clients.idempotency import (
    begin_idempotent_request,
    complete_idempotent_request,
)
from apps.webhooks.serializers import (
    WebhookEndpointCreateSerializer,
    WebhookTestSerializer,
    serialize_webhook_endpoint,
)
from common.permissions import IsTenantUser
from common.responses import success_response
from apps.webhooks.models import WebhookEndpoint


class WebhookSecretRotationConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The previous webhook signing secret overlap is still active."
    default_code = "webhook_secret_rotation_conflict"


class WebhookSecretRotationReplayConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This rotation response is obsolete because the secret was rotated again."
    default_code = "webhook_secret_rotation_replay_conflict"


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

    @transaction.atomic
    def post(self, request):
        idempotency_result = begin_idempotent_request(
            request=request,
            tenant=request.user.tenant,
            operation="webhook_endpoint.create",
        )
        if idempotency_result.is_replay:
            return success_response(
                idempotency_result.response_data,
                request=request,
                status=idempotency_result.response_status,
            )
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
        response_data = {
            "id": endpoint.public_id,
            "secret": endpoint._raw_secret,
            "status": endpoint.status,
        }
        complete_idempotent_request(
            idempotency_result,
            response_data=response_data,
            response_status=status.HTTP_201_CREATED,
        )
        return success_response(
            response_data,
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

    def obj(self, request, webhook_id, *, for_update=False):
        endpoints = WebhookEndpoint.objects
        if for_update:
            endpoints = endpoints.select_for_update()
        return get_object_or_404(
            endpoints, tenant=request.user.tenant, public_id=webhook_id
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
        endpoint.save(update_fields=["url", "description", "events_json", "updated_at"])
        return success_response(serialize_webhook_endpoint(endpoint), request=request)


class WebhookEndpointActionView(WebhookEndpointDetailView):
    fixed_action: str | None = None

    @transaction.atomic
    def post(self, request, webhook_id, action=None):
        action = self.fixed_action or action
        idempotency_result = None
        if action == "rotate":
            idempotency_result = begin_idempotent_request(
                request=request,
                tenant=request.user.tenant,
                operation="webhook_endpoint.rotate",
            )
            if idempotency_result.is_replay:
                endpoint = self.obj(request, webhook_id, for_update=True)
                replay_version = (
                    idempotency_result.response_data.get("signing_secret_version")
                    if isinstance(idempotency_result.response_data, dict)
                    else None
                )
                if replay_version != endpoint.signing_secret_version:
                    raise WebhookSecretRotationReplayConflict()
                return success_response(
                    idempotency_result.response_data,
                    request=request,
                    status=idempotency_result.response_status,
                )
        endpoint = self.obj(request, webhook_id, for_update=action == "rotate")
        if action == "disable":
            endpoint.status = "disabled"
        elif action == "reactivate":
            endpoint.status = "active"
        elif action == "rotate":
            if endpoint.previous_secret_overlap_active:
                raise WebhookSecretRotationConflict()
            raw_secret = WebhookEndpoint.generate_secret()
            endpoint.rotate_secret(
                raw_secret,
                previous_secret_expires_at=timezone.now()
                + timedelta(seconds=settings.WEBHOOK_SECRET_ROTATION_OVERLAP_SECONDS),
            )
            endpoint.save(
                update_fields=[
                    "secret_hash",
                    "signing_key",
                    "previous_signing_key",
                    "signing_secret_version",
                    "previous_secret_expires_at",
                    "updated_at",
                ]
            )
            record_audit_event(
                tenant=request.user.tenant,
                actor=request.user,
                request=request,
                action="webhook_endpoint.rotate",
                target_type="webhook_endpoint",
                target_id=endpoint.public_id,
                metadata={
                    "signing_secret_version": endpoint.signing_secret_version,
                    "previous_secret_expires_at": endpoint.previous_secret_expires_at.isoformat(),
                },
            )
            response_data = {
                **serialize_webhook_endpoint(endpoint),
                "secret": raw_secret,
            }
            complete_idempotent_request(
                idempotency_result,
                response_data=response_data,
                response_status=status.HTTP_200_OK,
            )
            return success_response(response_data, request=request)
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
