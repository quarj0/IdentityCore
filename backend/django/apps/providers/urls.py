from django.urls import path

from apps.providers.views import ProviderCheckListView, ProviderListView


urlpatterns = [
    path("", ProviderListView.as_view(), name="provider-list"),
    path("checks/", ProviderCheckListView.as_view(), name="provider-check-list"),
]
