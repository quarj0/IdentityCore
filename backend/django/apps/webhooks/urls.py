from common.public_api import public_api_path

from apps.webhooks.views import (
    WebhookEndpointActionView,
    WebhookEndpointDetailView,
    WebhookEndpointListCreateView,
    WebhookEndpointTestView,
)

urlpatterns = [
    public_api_path(
        "",
        WebhookEndpointListCreateView.as_view(),
        methods=("GET", "POST"),
        name="webhook-endpoint-list-create",
    ),
    public_api_path(
        "<str:webhook_id>/test",
        WebhookEndpointTestView.as_view(),
        methods=("POST",),
        name="webhook-endpoint-test",
    ),
    public_api_path(
        "<str:webhook_id>",
        WebhookEndpointDetailView.as_view(),
        methods=("GET", "PATCH"),
    ),
    public_api_path(
        "<str:webhook_id>/<str:action>",
        WebhookEndpointActionView.as_view(),
        methods=("POST",),
    ),
]
