"""Permission-gated customer key configuration; secret tokens are write-only."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.tenants.models import TenantKMSBinding
from common.authorization import AuthorizationAction, decide_user_access
from common.customer_kms import activate, disable, validate_arn
from common.responses import success_response


def tenant_for_keys(request):
    user = request.user
    tenant = getattr(user, "tenant", None)
    if (
        tenant is None
        or getattr(user, "is_platform_admin", False)
        or not decide_user_access(
            user,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=tenant,
            permission_code="manage_encryption",
        ).allowed
        or tenant.status != "active"
        or tenant.deleted_at is not None
    ):
        raise PermissionDenied("Customer key administration permission is required.")
    return tenant


class KMSInput(serializers.Serializer):
    environment = serializers.ChoiceField(choices=["sandbox", "production"])
    key_arn = serializers.CharField(max_length=255)
    grant_tokens = serializers.JSONField(required=False, default=list, write_only=True)

    def validate_key_arn(self, value):
        try:
            validate_arn(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from None
        return value

    def validate_grant_tokens(self, value):
        if (
            not isinstance(value, list)
            or len(value) > 10
            or any(
                not isinstance(item, str) or not 1 <= len(item) <= 4096
                for item in value
            )
        ):
            raise serializers.ValidationError("Use at most ten bounded grant tokens.")
        return value


def summary(binding):
    return {
        "id": binding.public_id,
        "environment": binding.environment,
        "key_arn": binding.key_arn,
        "status": binding.status,
        "active": binding.active,
        "validated_at": (
            binding.validated_at.isoformat() if binding.validated_at else None
        ),
    }


class TenantKMSListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = tenant_for_keys(request)
        return success_response(
            {
                "bindings": [
                    summary(binding)
                    for binding in TenantKMSBinding.objects.filter(
                        tenant=tenant, deleted_at__isnull=True
                    ).order_by("-created_at", "-pk")[:100]
                ]
            },
            request=request,
        )

    @transaction.atomic
    def post(self, request):
        tenant = tenant_for_keys(request)
        serializer = KMSInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        lock_audit_chain(tenant.pk)
        if (
            TenantKMSBinding.objects.filter(
                tenant=tenant, deleted_at__isnull=True
            ).count()
            >= 100
        ):
            raise ValidationError(
                "A tenant can retain at most 100 customer key bindings."
            )
        data = serializer.validated_data
        binding = TenantKMSBinding.objects.create(
            tenant=tenant,
            environment=data["environment"],
            key_arn=data["key_arn"],
            grant_tokens_json=data["grant_tokens"],
        )
        record_audit_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="encryption.kms_configured",
            target_type="tenant_kms_binding",
            target_id=binding.public_id,
            metadata={"environment": binding.environment, "key_arn": binding.key_arn},
        )
        return success_response(summary(binding), request=request, status=201)


class TenantKMSActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, binding_id, action):
        tenant = tenant_for_keys(request)
        binding = get_object_or_404(
            TenantKMSBinding,
            tenant=tenant,
            public_id=binding_id,
            deleted_at__isnull=True,
        )
        if action == "activate":
            try:
                binding, job = activate(binding, actor=request.user, request=request)
            except ValueError:
                raise ValidationError(
                    "Customer key validation or activation failed."
                ) from None
            return success_response(
                {**summary(binding), "rotation_id": job.public_id}, request=request
            )
        if action == "disable":
            binding = disable(binding, actor=request.user, request=request)
            return success_response(summary(binding), request=request)
        raise ValidationError("Use activate or disable.")
