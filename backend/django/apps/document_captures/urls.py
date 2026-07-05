from django.urls import path

from apps.document_captures.views import DocumentCaptureDownloadURLView


urlpatterns = [
    path(
        "<str:capture_id>/download-url",
        DocumentCaptureDownloadURLView.as_view(),
        name="document-capture-download-url",
    ),
]
