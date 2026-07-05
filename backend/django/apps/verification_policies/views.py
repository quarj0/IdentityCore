from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.verification_policies.serializers import (
    VerificationPolicyCreateSerializer,
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
