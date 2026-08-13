from common.public_api import public_api_path

from apps.api_clients.views import (
    APIClientActionView,
    APIClientDetailView,
    APIClientListCreateView,
)

urlpatterns = [
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
