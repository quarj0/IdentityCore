from django.urls import path

from apps.api_clients.views import APIClientListCreateView


urlpatterns = [
    path("", APIClientListCreateView.as_view(), name="api-client-list-create"),
]
