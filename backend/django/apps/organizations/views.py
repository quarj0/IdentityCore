from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.organizations.serializers import (
    OrganizationBrandingAssetUploadSerializer,
    OrganizationBrandingUpdateSerializer,
    serialize_organization,
)
from apps.organizations.services import update_organization_branding_settings
from common.permissions import IsTenantUser
from common.responses import success_response


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
            branding_image_storage_keys=serializer.validated_data.get("branding_image_storage_keys"),
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
            serializer.save(),
            request=request,
            status=status.HTTP_201_CREATED,
        )
