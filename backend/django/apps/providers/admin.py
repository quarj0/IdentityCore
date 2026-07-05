from django.contrib import admin

from apps.providers.models import Provider, ProviderCheck


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("public_id", "name", "code", "provider_type", "status")
    list_filter = ("provider_type", "status")
    search_fields = ("public_id", "name", "code")


@admin.register(ProviderCheck)
class ProviderCheckAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "verification", "provider", "check_type", "status", "started_at")
    list_filter = ("check_type", "status", "provider__provider_type")
    search_fields = ("public_id", "provider_reference", "verification__public_id", "provider__code")
