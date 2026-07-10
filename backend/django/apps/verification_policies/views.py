from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.audit.services import record_audit_event
from apps.verification_policies.models import VerificationPolicy
from apps.verification_policies.serializers import (
    VerificationPolicyCreateSerializer,
    VerificationPolicyUpdateSerializer,
    serialize_verification_policy,
)
from common.permissions import IsTenantUser
from common.responses import success_response


class VerificationPolicyListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        policies = request.user.tenant.verification_policies.order_by("name", "-version")
        return success_response(
            [serialize_verification_policy(policy) for policy in policies],
            request=request,
        )

    def post(self, request):
        serializer = VerificationPolicyCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        policy = serializer.save()
        record_audit_event(
            tenant=request.user.tenant, actor=request.user, request=request,
            action="verification_policy.created", target_type="verification_policy",
            target_id=policy.public_id, metadata={"version": policy.version},
        )
        return success_response(
            {
                "id": policy.public_id,
                "name": policy.name,
                "version": policy.version,
                "status": policy.status,
            },
            request=request,
            status=status.HTTP_201_CREATED,
        )


class VerificationPolicyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get_object(self, request, policy_id):
        return get_object_or_404(
            request.user.tenant.verification_policies, public_id=policy_id
        )

    def get(self, request, policy_id):
        return success_response(
            serialize_verification_policy(self.get_object(request, policy_id)),
            request=request,
        )

    def patch(self, request, policy_id):
        policy = self.get_object(request, policy_id)
        serializer = VerificationPolicyUpdateSerializer(
            policy, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        policy = serializer.save()
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="verification_policy.updated",
            target_type="verification_policy",
            target_id=policy.public_id,
            metadata={"version": policy.version},
        )
        return success_response(serialize_verification_policy(policy), request=request)


class VerificationPolicyCloneView(VerificationPolicyDetailView):
    def post(self, request, policy_id):
        source = self.get_object(request, policy_id)
        latest = source.tenant.verification_policies.filter(name=source.name).order_by("-version").first()
        clone = VerificationPolicy.objects.create(
            tenant=source.tenant,
            name=source.name,
            description=source.description,
            version=(latest.version + 1),
            status="draft",
            required_document_types_json=source.required_document_types,
            required_liveness_level=source.required_liveness_level,
            face_match_threshold=source.face_match_threshold,
            manual_review_threshold=source.manual_review_threshold,
            verification_expiry_minutes=source.verification_expiry_minutes,
            media_retention_days=source.media_retention_days,
            metadata_retention_days=source.metadata_retention_days,
            created_by=request.user,
        )
        record_audit_event(
            tenant=source.tenant, actor=request.user, request=request,
            action="verification_policy.cloned", target_type="verification_policy",
            target_id=clone.public_id, metadata={"source_id": source.public_id},
        )
        return success_response(serialize_verification_policy(clone), request=request, status=status.HTTP_201_CREATED)


class VerificationPolicyActivateView(VerificationPolicyDetailView):
    @transaction.atomic
    def post(self, request, policy_id):
        policy = self.get_object(request, policy_id)
        if policy.status != "draft":
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"status": "Only draft templates can be activated."})
        policy.tenant.verification_policies.filter(name=policy.name, status="active").update(status="archived")
        policy.status = "active"
        policy.save(update_fields=["status", "updated_at"])
        record_audit_event(
            tenant=policy.tenant, actor=request.user, request=request,
            action="verification_policy.activated", target_type="verification_policy",
            target_id=policy.public_id, metadata={"version": policy.version},
        )
        return success_response(serialize_verification_policy(policy), request=request)


class VerificationPolicyArchiveView(VerificationPolicyDetailView):
    def post(self, request, policy_id):
        policy = self.get_object(request, policy_id)
        if policy.status == "archived":
            return success_response(serialize_verification_policy(policy), request=request)
        policy.status = "archived"
        policy.save(update_fields=["status", "updated_at"])
        record_audit_event(
            tenant=policy.tenant, actor=request.user, request=request,
            action="verification_policy.archived", target_type="verification_policy",
            target_id=policy.public_id, metadata={"version": policy.version},
        )
        return success_response(serialize_verification_policy(policy), request=request)
