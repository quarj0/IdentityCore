from common.public_api import public_api_path, internal_api_path
from apps.providers import assurance_views, operation_views

from apps.providers.views import (
    ProviderCheckListView,
    ProviderHealthView,
    ProviderListView,
)


from apps.providers.setup_views import (
    ProviderSetupView,
    ProviderConfigurationListView,
    ProviderConfigurationActionView,
)

urlpatterns = [
    public_api_path(
        "operations",
        operation_views.OperationListView.as_view(),
        methods=("GET",),
        name="provider-operation-list",
    ),
    public_api_path(
        "operations/<str:operation_id>",
        operation_views.OperationDetailView.as_view(),
        methods=("GET",),
        name="provider-operation-detail",
    ),
    public_api_path(
        "operations/<str:operation_id>/cancel",
        operation_views.OperationCancelView.as_view(),
        methods=("POST",),
        name="provider-operation-cancel",
    ),
    public_api_path(
        "operations/<str:operation_id>/callback",
        operation_views.ProviderCallbackView.as_view(),
        methods=("POST",),
        name="provider-operation-callback",
    ),
    public_api_path(
        "certifications/scope",
        assurance_views.CertificationScopeView.as_view(),
        methods=("GET",),
        name="provider-certification-scope",
    ),
    public_api_path(
        "certifications",
        assurance_views.CertificationListView.as_view(),
        methods=("GET", "POST"),
        name="provider-certification-list",
    ),
    public_api_path(
        "certifications/<str:certification_id>",
        assurance_views.CertificationDetailView.as_view(),
        methods=("GET",),
        name="provider-certification-detail",
    ),
    public_api_path(
        "certifications/<str:certification_id>/approve",
        assurance_views.CertificationApproveView.as_view(),
        methods=("POST",),
        name="provider-certification-approve",
    ),
    public_api_path(
        "certifications/<str:certification_id>/revoke",
        assurance_views.CertificationRevokeView.as_view(),
        methods=("POST",),
        name="provider-certification-revoke",
    ),
    internal_api_path("setup/", ProviderSetupView.as_view(), name="provider-setup"),
    internal_api_path(
        "<str:provider_id>/configurations/",
        ProviderConfigurationListView.as_view(),
        name="provider-configuration-list",
    ),
    internal_api_path(
        "configurations/<str:configuration_id>/<str:action>/",
        ProviderConfigurationActionView.as_view(),
        name="provider-configuration-action",
    ),
    internal_api_path("", ProviderListView.as_view(), name="provider-list"),
    internal_api_path(
        "checks/", ProviderCheckListView.as_view(), name="provider-check-list"
    ),
    internal_api_path("health/", ProviderHealthView.as_view(), name="provider-health"),
]
