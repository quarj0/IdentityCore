from django.contrib import admin

from apps.webhooks.models import WebhookDeliveryAttempt, WebhookEndpoint, WebhookEvent


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "url", "status", "created_at")
    list_filter = ("tenant", "status")
    search_fields = ("public_id", "url")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "webhook_endpoint", "event_type", "status", "created_at")
    list_filter = ("tenant", "status", "event_type")
    search_fields = ("public_id", "event_type", "webhook_endpoint__public_id")


@admin.register(WebhookDeliveryAttempt)
class WebhookDeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ("webhook_event", "status_code", "attempted_at", "duration_ms")
    search_fields = ("webhook_event__public_id", "error_message")
