from common.public_api import public_api_path

from apps.organizations.views import (
    OrganizationBrandingAssetUploadView,
    OrganizationDetailView,
    WorkspaceSuspendView,
    OrganizationDocumentDeleteView,
    OrganizationDocumentContentUploadView,
    OrganizationDocumentUploadView,
    OrganizationDocumentUploadCompleteView,
)

urlpatterns = [
    public_api_path(
        "me/",
        OrganizationDetailView.as_view(),
        methods=("GET", "PATCH"),
        name="organization-detail",
    ),
    public_api_path("me/suspend", WorkspaceSuspendView.as_view(), methods=("POST",)),
    public_api_path(
        "me/verification-documents/upload/",
        OrganizationDocumentUploadView.as_view(),
        methods=("POST",),
    ),
    public_api_path(
        "me/verification-documents/<str:document_id>/content/",
        OrganizationDocumentContentUploadView.as_view(),
        methods=("PUT",),
        name="organization-document-content-upload",
    ),
    public_api_path(
        "me/verification-documents/<str:document_id>/complete/",
        OrganizationDocumentUploadCompleteView.as_view(),
        methods=("POST",),
    ),
    public_api_path(
        "me/verification-documents/<str:document_id>/",
        OrganizationDocumentDeleteView.as_view(),
        methods=("DELETE",),
    ),
    public_api_path(
        "me/branding/assets/upload/",
        OrganizationBrandingAssetUploadView.as_view(),
        methods=("POST",),
        name="organization-branding-asset-upload",
    ),
]
