from django.contrib import admin

from apps.api_clients.models import APIClient


@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):
    list_display = ("name", "public_id", "client_id", "tenant", "status", "last_used_at")
    list_filter = ("status", "tenant")
    search_fields = ("name", "public_id", "client_id", "tenant__name")
