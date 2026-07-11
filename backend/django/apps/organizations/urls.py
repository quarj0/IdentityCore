from django.urls import path

from apps.organizations.views import (
    OrganizationBrandingAssetUploadView,
    OrganizationDetailView,
    WorkspaceSuspendView,
)

urlpatterns = [
    path("me/", OrganizationDetailView.as_view(), name="organization-detail"),
    path("me/suspend", WorkspaceSuspendView.as_view()),
    path(
        "me/branding/assets/upload/",
        OrganizationBrandingAssetUploadView.as_view(),
        name="organization-branding-asset-upload",
    ),
]
