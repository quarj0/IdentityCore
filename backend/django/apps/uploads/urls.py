from django.urls import path

from apps.uploads.views import UploadCreateView


urlpatterns = [
    path("", UploadCreateView.as_view(), name="upload-create"),
]
