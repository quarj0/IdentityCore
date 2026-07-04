from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from apps.verifications.serializers import (
    VerificationCancelSerializer,
    VerificationCreateSerializer,
    paginate_results,
    serialize_verification,
    serialize_verification_summary,
)
from apps.verifications.models import Verification, VerificationStatus
from common.authentication import APIClientAuthentication
from common.permissions import HasAPIClientScopes
from common.responses import success_response


class VerificationListCreateView(APIView):
    authentication_classes = [APIClientAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_scopes = ("verifications:read",)
        else:
            self.required_scopes = ("verifications:create",)
        return [HasAPIClientScopes()]

    def get(self, request):
        verifications = request.tenant.verifications.select_related("verification_subject").order_by("-created_at")

        status_value = request.query_params.get("status")
        external_reference = request.query_params.get("external_reference")
        if status_value:
            verifications = verifications.filter(status=status_value)
        if external_reference:
            verifications = verifications.filter(external_reference=external_reference)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_obj, pagination = paginate_results(verifications, page, page_size)
        return success_response(
            {
                "results": [serialize_verification_summary(item) for item in page_obj.object_list],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        serializer = VerificationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        verification = serializer.save()
        session = verification._initial_session
        return success_response(
            {
                "id": verification.public_id,
                "status": verification.status,
                "verification_url": verification._verification_url,
                "session_id": session.public_id,
                "expires_at": verification.expires_at.isoformat(),
            },
            request=request,
            status=status.HTTP_201_CREATED,
        )


class VerificationDetailView(APIView):
    authentication_classes = [APIClientAuthentication]
    required_scopes = ("verifications:read",)
    permission_classes = [HasAPIClientScopes]

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject"),
            tenant=request.tenant,
            public_id=verification_id,
        )
        return success_response(serialize_verification(verification), request=request)


class VerificationCancelView(APIView):
    authentication_classes = [APIClientAuthentication]
    required_scopes = ("verifications:create",)
    permission_classes = [HasAPIClientScopes]

    def post(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification,
            tenant=request.tenant,
            public_id=verification_id,
        )
        serializer = VerificationCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification.status = VerificationStatus.CANCELLED
        verification.cancelled_at = timezone.now()
        verification.save(update_fields=["status", "cancelled_at", "updated_at"])
        return success_response(
            {
                "id": verification.public_id,
                "status": verification.status,
            },
            request=request,
        )
