from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "tenant",
        "recipient_type",
        "recipient",
        "channel",
        "status",
        "created_at",
    )
    list_filter = ("tenant", "recipient_type", "channel", "status")
    search_fields = ("public_id", "recipient", "template_code", "provider_reference")
