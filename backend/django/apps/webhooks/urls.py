from django.urls import path

from apps.webhooks.views import WebhookEndpointListCreateView, WebhookEndpointTestView


urlpatterns = [
    path("", WebhookEndpointListCreateView.as_view(), name="webhook-endpoint-list-create"),
    path("<str:webhook_id>/test", WebhookEndpointTestView.as_view(), name="webhook-endpoint-test"),
]
