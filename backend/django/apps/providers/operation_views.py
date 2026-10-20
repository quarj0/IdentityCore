"""Provider callbacks authenticate the exact wire body, never a dashboard session."""

import json

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import JsonResponse
from redis.exceptions import RedisError
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.evidence.services import _scope, _audit, _transition
from apps.evidence.views import GovernedAPIView
from apps.providers.adapters import ProviderContractError
from apps.providers.configuration import _signing_context
from apps.providers.models import ProviderOperation
from apps.providers import operations
from apps.verifications.processing_jobs import (
    ProcessingJobOwnershipLost,
    ProcessingConsentProofUnavailable,
)
from common.provider_signing import ProviderSignatureError, verify_message, sign_message
from common.responses import success_response, error_response, success_payload
from django.utils import timezone
from rest_framework import serializers
from apps.evidence.serializers import StrictInput


class OperationQuery(serializers.Serializer):
    project_id = serializers.CharField(max_length=64)


class OperationCancelInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    reason = serializers.RegexField(r"^[a-z][a-z0-9_]{0,119}$")


class ProviderCallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "sensitive_public"

    def post(self, request, operation_id):
        from apps.providers.operations import _related

        record = _related().filter(public_id=operation_id).first()
        body = request.body
        if record is None or len(body) > 256 * 1024 or request.query_params:
            raise PermissionDenied("Provider callback authentication failed.")
        try:
            context = _signing_context(record.configuration)
        except (ValueError, KeyError):
            return error_response(
                "provider_callback_unavailable",
                "Provider callback authentication is temporarily unavailable.",
                request=request,
                status=503,
            )
        if context is None:
            raise PermissionDenied("Provider callback authentication failed.")
        try:
            signed = verify_message(
                method="POST",
                path=request.path,
                body=body,
                headers=request.headers,
                keys={context.key_id: context.secret},
                replay_namespace=f"provider-callback:{record.public_id}:{context.key_id}",
            )
        except ProviderSignatureError:
            raise PermissionDenied("Provider callback authentication failed.") from None
        except RedisError:
            return error_response(
                "provider_callback_unavailable",
                "Provider callback authentication is temporarily unavailable.",
                request=request,
                status=503,
            )
        try:
            response = json.loads(body)
            if request.content_type != "application/json":
                raise ValueError()
            record = operations.accept_response(
                record.public_id, response, configuration_id=record.configuration_id
            )
        except ProcessingConsentProofUnavailable:
            return error_response(
                "provider_callback_unavailable",
                "Current consent proof is temporarily unavailable.",
                request=request,
                status=503,
            )
        except (
            ValueError,
            TypeError,
            ProviderContractError,
            ProcessingJobOwnershipLost,
            ValidationError,
            DjangoValidationError,
        ):
            return error_response(
                "provider_callback_rejected",
                "Provider completion is unavailable or does not match its admitted operation.",
                request=request,
                status=409,
            )
        data = success_payload(
            {"id": record.public_id, "status": record.status}, request=request
        )
        # Response bytes must be signed after serialization, using the request nonce.
        result = JsonResponse(data)
        result["Cache-Control"] = "no-store"
        for key, value in (
            sign_message(
                method="POST",
                path=request.path,
                body=result.content,
                key_id=context.key_id,
                secret=context.secret,
                nonce=signed.nonce,
            )
            .headers()
            .items()
        ):
            result[key] = value
        return result


def operation_summary(record):
    return {
        "id": record.public_id,
        "status": record.status,
        "configuration_id": record.configuration.public_id,
        "check_id": record.provider_check.public_id,
        "verification_id": record.verification.public_id,
        "capability": record.capability,
        "deadline": record.deadline.isoformat(),
        "delete_after": record.delete_after.isoformat(),
        "completed_at": record.completed_at.isoformat()
        if record.completed_at
        else None,
        "invalidation_reason": record.invalidation_reason,
        "remote_action": record.remote_action or None,
        "remote_action_status": record.remote_action_status or None,
        "remote_requested_at": record.remote_requested_at.isoformat()
        if record.remote_requested_at
        else None,
        "remote_attempted_at": record.remote_attempted_at.isoformat()
        if record.remote_attempted_at
        else None,
    }


class OperationListQuery(OperationQuery):
    verification_id = serializers.CharField(max_length=64, required=False)
    status = serializers.ChoiceField(
        choices=["created", "pending", "completed", "failed", "cancelled", "expired"],
        required=False,
    )
    capability = serializers.CharField(max_length=32, required=False)


class OperationListView(GovernedAPIView):
    read_permission = "providers:operations"

    @transaction.atomic
    def get(self, request):
        data = self.parsed(OperationListQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data.pop("project_id"))
        from apps.evidence.access import current_actor
        from common.pagination import paginate_cursor_results

        actor = current_actor(
            self.actor(request), tenant, "providers:operations", project=project
        )
        query = ProviderOperation.objects.select_related(
            "configuration", "provider_check", "verification"
        ).filter(tenant=tenant, project=project)
        if data.get("verification_id"):
            query = query.filter(verification__public_id=data["verification_id"])
        for key in ("status", "capability"):
            if key in data:
                query = query.filter(**{key: data[key]})
        items, pagination = paginate_cursor_results(
            query,
            request,
            cursor_scope=f"provider-operations:{tenant.public_id}:{project.public_id}:{actor.public_id}",
        )
        return success_response(
            {
                "results": [operation_summary(item) for item in items],
                "pagination": pagination,
            },
            request=request,
        )


class OperationDetailView(GovernedAPIView):
    read_permission = "providers:operations"
    write_permission = "providers:operations"

    @transaction.atomic
    def get(self, request, operation_id):
        data = self.parsed(OperationQuery, request.query_params)
        tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
        from apps.evidence.access import current_actor

        current_actor(
            self.actor(request), tenant, "providers:operations", project=project
        )
        from django.shortcuts import get_object_or_404

        record = get_object_or_404(
            ProviderOperation.objects.select_related(
                "configuration", "provider_check", "verification"
            ),
            tenant=tenant,
            project=project,
            public_id=operation_id,
        )
        return success_response(operation_summary(record), request=request)


class OperationCancelView(OperationDetailView):
    def post(self, request, operation_id):
        data = self.parsed(OperationCancelInput, request.data)

        def cancel():
            tenant, project, _ = _scope(self.tenant(request).pk, data["project_id"])
            from apps.evidence.access import current_actor

            current_actor(
                self.actor(request), tenant, "providers:operations", project=project
            )
            from django.shortcuts import get_object_or_404

            record = get_object_or_404(
                ProviderOperation,
                tenant=tenant,
                project=project,
                public_id=operation_id,
            )
            if record.status not in operations.TERMINAL:
                _transition(
                    record,
                    status="cancelled",
                    completed_at=timezone.now(),
                    invalidation_reason=data["reason"],
                    remote_action="cancel",
                    remote_action_status="pending",
                    remote_requested_at=timezone.now(),
                )
                _audit(
                    record,
                    self.actor(request),
                    "provider.operation_cancelled",
                    request,
                    reason=data["reason"],
                )
            return {"id": record.public_id, "status": record.status}

        return self.write(
            request, f"providers.operation.cancel:{operation_id}", cancel, status=200
        )
