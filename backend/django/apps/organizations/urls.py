from django.urls import path

from apps.organizations.views import (
    OrganizationBrandingAssetUploadView,
    OrganizationDetailView,
    WorkspaceSuspendView,
    OrganizationDocumentDeleteView,
    OrganizationDocumentUploadView,
    OrganizationDocumentUploadCompleteView,
    OrganizationDocumentUploadTransferView,
)

urlpatterns = [
    path("me/", OrganizationDetailView.as_view(), name="organization-detail"),
    path("me/suspend", WorkspaceSuspendView.as_view()),
    path(
        "me/verification-documents/upload/",
        OrganizationDocumentUploadView.as_view(),
        name="organization-document-upload",
    ),
    path(
        "me/verification-documents/<str:document_id>/transfer/",
        OrganizationDocumentUploadTransferView.as_view(),
        name="organization-document-upload-transfer",
    ),
    path(
        "me/verification-documents/<str:document_id>/complete/",
        OrganizationDocumentUploadCompleteView.as_view(),
        name="organization-document-upload-complete",
    ),
    path(
        "me/verification-documents/<str:document_id>/",
        OrganizationDocumentDeleteView.as_view(),
        name="organization-document-delete",
    ),
    path(
        "me/branding/assets/upload/",
        OrganizationBrandingAssetUploadView.as_view(),
        name="organization-branding-asset-upload",
    ),
]
