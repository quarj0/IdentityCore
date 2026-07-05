from django.urls import path

from apps.biometrics.views import SelfieCaptureDownloadURLView


urlpatterns = [
    path(
        "selfie-captures/<str:selfie_id>/download-url",
        SelfieCaptureDownloadURLView.as_view(),
        name="selfie-capture-download-url",
    ),
]
