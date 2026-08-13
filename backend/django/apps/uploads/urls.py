from apps.uploads.views import UploadCompleteView, UploadCreateView, UploadTransferView
from common.public_api import public_api_path


urlpatterns = [
    public_api_path(
        "", UploadCreateView.as_view(), methods=("POST",), name="upload-create"
    ),
    public_api_path(
        "<str:upload_id>/transfer",
        UploadTransferView.as_view(),
        methods=("POST",),
        name="upload-transfer",
    ),
    public_api_path(
        "<str:upload_id>/complete",
        UploadCompleteView.as_view(),
        methods=("POST",),
        name="upload-complete",
    ),
]
