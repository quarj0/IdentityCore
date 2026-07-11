from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.organizations.serializers import (
    OrganizationBrandingAssetUploadSerializer,
    OrganizationBrandingUpdateSerializer,
    OrganizationDocumentUploadSerializer,
    serialize_organization,
)
from apps.organizations.services import update_organization_branding_settings
from common.permissions import IsTenantUser
from common.responses import success_response
from apps.audit.services import record_audit_event
from apps.organizations.models import OrganizationStatus, OrganizationSupportingDocument
from apps.tenants.models import TenantStatus
from apps.verifications.models import VerificationSessionStatus
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        return success_response(
            serialize_organization(request.user.tenant.organization),
            request=request,
        )

    def patch(self, request):
        serializer = OrganizationBrandingUpdateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        organization = update_organization_branding_settings(
            organization=request.user.tenant.organization,
            logo_storage_key=serializer.validated_data.get("logo_storage_key"),
            branding_image_storage_keys=serializer.validated_data.get(
                "branding_image_storage_keys"
            ),
        )
        return success_response(
            serialize_organization(organization),
            request=request,
            status=status.HTTP_200_OK,
        )


class OrganizationBrandingAssetUploadView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def post(self, request):
        serializer = OrganizationBrandingAssetUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return success_response(
            serializer.save(), request=request, status=status.HTTP_201_CREATED
        )


class OrganizationDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]
    def post(self, request):
        serializer = OrganizationDocumentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return success_response(serializer.save(), request=request, status=status.HTTP_201_CREATED)


class OrganizationDocumentUploadCompleteView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]
    def post(self, request, document_id):
        document = get_object_or_404(OrganizationSupportingDocument.objects,
            public_id=document_id, tenant=request.user.tenant, organization=request.user.tenant.organization,
            status="initiated", deleted_at__isnull=True,
        )
        document.status = "uploaded"
        document.save(update_fields=["status", "updated_at"])
        return success_response({"document_id": document.public_id, "status": document.status}, request=request)


class WorkspaceSuspendView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def post(self, request):
        tenant = request.user.tenant
        organization = tenant.organization
        if request.data.get("confirmation") != organization.name:
            return success_response(
                {
                    "detail": "Type the organization name exactly to suspend this workspace."
                },
                request=request,
                status=400,
            )
        organization.status = OrganizationStatus.SUSPENDED
        organization.save(update_fields=["status", "updated_at"])
        tenant.status = TenantStatus.SUSPENDED
        tenant.save(update_fields=["status", "updated_at"])
        tenant.api_clients.exclude(status="revoked").update(status="disabled")
        tenant.webhook_endpoints.exclude(status="disabled").update(status="disabled")
        tenant.verification_sessions.filter(status__in=["created", "active"]).update(
            status=VerificationSessionStatus.REVOKED
        )
        for token in OutstandingToken.objects.filter(user__tenant=tenant):
            BlacklistedToken.objects.get_or_create(token=token)
        record_audit_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="workspace.suspended",
            target_type="tenant",
            target_id=tenant.public_id,
        )
        return success_response({"suspended": True}, request=request)
