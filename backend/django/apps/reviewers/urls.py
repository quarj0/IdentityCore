from django.urls import path

from apps.reviewers.views import (
    PlatformAPIClientDetailView,
    PlatformAPIClientListView,
    PlatformAuditEventDetailView,
    PlatformAuditEventListView,
    PlatformProviderDetailView,
    PlatformProviderListView,
    PlatformVerificationPolicyDetailView,
    PlatformVerificationPolicyListView,
    PlatformWebhookEndpointDetailView,
    PlatformWebhookEndpointListView,
)

urlpatterns = [
    path("audit-events/", PlatformAuditEventListView.as_view()),
    path("audit-events/<str:event_id>", PlatformAuditEventDetailView.as_view()),
    path("providers/", PlatformProviderListView.as_view()),
    path("providers/<str:provider_id>", PlatformProviderDetailView.as_view()),
    path("policies/", PlatformVerificationPolicyListView.as_view()),
    path("policies/<str:policy_id>", PlatformVerificationPolicyDetailView.as_view()),
    path("api-clients/", PlatformAPIClientListView.as_view()),
    path("api-clients/<str:client_id>", PlatformAPIClientDetailView.as_view()),
    path("webhooks/", PlatformWebhookEndpointListView.as_view()),
    path("webhooks/<str:webhook_id>", PlatformWebhookEndpointDetailView.as_view()),
]
