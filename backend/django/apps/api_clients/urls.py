from django.urls import path

from apps.api_clients.views import (
    APIClientActionView,
    APIClientDetailView,
    APIClientListCreateView,
)

urlpatterns = [
    path("", APIClientListCreateView.as_view(), name="api-client-list-create"),
    path("<str:client_id>", APIClientDetailView.as_view()),
    path("<str:client_id>/<str:action>", APIClientActionView.as_view()),
]
