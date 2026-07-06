from django.urls import path

from apps.organizations.views import (
    OrganizationBrandingAssetUploadView,
    OrganizationDetailView,
)


urlpatterns = [
    path("me/", OrganizationDetailView.as_view(), name="organization-detail"),
    path(
        "me/branding/assets/upload/",
        OrganizationBrandingAssetUploadView.as_view(),
        name="organization-branding-asset-upload",
    ),
]
