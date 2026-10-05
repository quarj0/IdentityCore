from common.fields import environment_for_instance
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.document_captures.models import DocumentCapture
from common.permissions import IsTenantUser
from common.responses import success_response
from common.storage import (
    build_signed_download_url,
    get_object_storage_media_bucket_name,
)


class DocumentCaptureDownloadURLView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, capture_id: str):
        capture = get_object_or_404(
            DocumentCapture.objects.select_related("tenant").exclude(status="deleted"),
            tenant=request.user.tenant,
            public_id=capture_id,
            deleted_at__isnull=True,
            identity_document__deleted_at__isnull=True,
            identity_document__verification__deleted_at__isnull=True,
            identity_document__verification_subject__deleted_at__isnull=True,
        )
        return success_response(
            {
                "id": capture.public_id,
                "download_url": build_signed_download_url(
                    storage_key=capture.storage_key,
                    tenant_scope=capture.tenant.public_id,
                    environment=environment_for_instance(capture),
                    bucket_name=get_object_storage_media_bucket_name(),
                ),
                "expires_in_seconds": 300,
            },
            request=request,
        )
