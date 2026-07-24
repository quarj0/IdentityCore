from django.urls import path

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
    path("me/", OrganizationDetailView.as_view(), name="organization-detail"),
    path("me/suspend", WorkspaceSuspendView.as_view()),
    path("me/verification-documents/upload/", OrganizationDocumentUploadView.as_view()),
    path("me/verification-documents/<str:document_id>/content/", OrganizationDocumentContentUploadView.as_view(), name="organization-document-content-upload"),
    path("me/verification-documents/<str:document_id>/complete/", OrganizationDocumentUploadCompleteView.as_view()),
    path("me/verification-documents/<str:document_id>/", OrganizationDocumentDeleteView.as_view()),
    path(
        "me/branding/assets/upload/",
        OrganizationBrandingAssetUploadView.as_view(),
        name="organization-branding-asset-upload",
    ),
]
