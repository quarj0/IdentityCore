from common.public_api import internal_api_path, public_api_path
from apps.api_clients.usage_views import APIUsageView

from apps.api_clients.views import (
    APIClientActionView,
    APIClientDetailView,
    APIClientListCreateView,
)

urlpatterns = [
    internal_api_path("usage", APIUsageView.as_view()),
    public_api_path(
        "",
        APIClientListCreateView.as_view(),
        methods=("GET", "POST"),
        name="api-client-list-create",
    ),
    public_api_path(
        "<str:client_id>", APIClientDetailView.as_view(), methods=("GET", "PATCH")
    ),
    public_api_path(
        "<str:client_id>/<str:action>",
        APIClientActionView.as_view(),
        methods=("POST",),
        name="api-client-action",
    ),
]
