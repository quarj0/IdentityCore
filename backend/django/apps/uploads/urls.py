from django.urls import path

from apps.uploads.views import UploadCreateView, UploadTransferView


urlpatterns = [
    path("", UploadCreateView.as_view(), name="upload-create"),
    path("<str:upload_id>/transfer", UploadTransferView.as_view(), name="upload-transfer"),
]
