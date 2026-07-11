from django.urls import path

from apps.webhooks.views import (
    WebhookEndpointActionView,
    WebhookEndpointDetailView,
    WebhookEndpointListCreateView,
    WebhookEndpointTestView,
)

urlpatterns = [
    path(
        "", WebhookEndpointListCreateView.as_view(), name="webhook-endpoint-list-create"
    ),
    path(
        "<str:webhook_id>/test",
        WebhookEndpointTestView.as_view(),
        name="webhook-endpoint-test",
    ),
    path("<str:webhook_id>", WebhookEndpointDetailView.as_view()),
    path("<str:webhook_id>/<str:action>", WebhookEndpointActionView.as_view()),
]
