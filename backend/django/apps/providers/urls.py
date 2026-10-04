from django.urls import path

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
    path("setup/", ProviderSetupView.as_view(), name="provider-setup"),
    path(
        "<str:provider_id>/configurations/",
        ProviderConfigurationListView.as_view(),
        name="provider-configuration-list",
    ),
    path(
        "configurations/<str:configuration_id>/<str:action>/",
        ProviderConfigurationActionView.as_view(),
        name="provider-configuration-action",
    ),
    path("", ProviderListView.as_view(), name="provider-list"),
    path("checks/", ProviderCheckListView.as_view(), name="provider-check-list"),
    path("health/", ProviderHealthView.as_view(), name="provider-health"),
]
