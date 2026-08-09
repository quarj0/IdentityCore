from django.urls import path

from apps.providers.views import (
    ProviderCheckListView,
    ProviderHealthView,
    ProviderListView,
)


urlpatterns = [
    path("", ProviderListView.as_view(), name="provider-list"),
    path("checks/", ProviderCheckListView.as_view(), name="provider-check-list"),
    path("health/", ProviderHealthView.as_view(), name="provider-health"),
]
