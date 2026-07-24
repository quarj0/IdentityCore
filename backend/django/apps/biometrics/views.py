from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.biometrics.models import SelfieCapture
from common.permissions import IsTenantUser
from common.responses import success_response
from common.storage import build_signed_download_url, get_object_storage_media_bucket_name


class SelfieCaptureDownloadURLView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request, selfie_id: str):
        selfie_capture = get_object_or_404(
            SelfieCapture.objects.select_related("tenant"),
            tenant=request.user.tenant,
            public_id=selfie_id,
        )
        return success_response(
            {
                "id": selfie_capture.public_id,
                "download_url": build_signed_download_url(
                    storage_key=selfie_capture.storage_key,
                    bucket_name=get_object_storage_media_bucket_name(),
                ),
                "expires_in_seconds": 300,
            },
            request=request,
        )
