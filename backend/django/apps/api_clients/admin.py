from django.contrib import admin
from django.db import transaction

from apps.api_clients.models import APIClient, APIUsageQuota
from apps.audit.services import record_audit_event


@admin.register(APIUsageQuota)
class APIUsageQuotaAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "environment",
        "requests_per_minute",
        "requests_per_month",
    )
    fields = ("tenant", "environment", "requests_per_minute", "requests_per_month")

    def get_readonly_fields(self, request, obj=None):
        return ("tenant", "environment") if obj else ()

    def has_delete_permission(self, request, obj=None):
        return False

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            APIUsageQuota.objects.select_for_update(no_key=True).get(pk=obj.pk)
        super().save_model(request, obj, form, change)
        record_audit_event(
            tenant=obj.tenant,
            actor=request.user,
            request=request,
            action="api.quota_configured",
            target_type="APIUsageQuota",
            target_id=str(obj.pk),
            metadata={
                "environment": obj.environment,
                "requests_per_minute": obj.requests_per_minute,
                "requests_per_month": obj.requests_per_month,
            },
        )


@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):
    list_display = ("name", "public_id", "client_id", "tenant", "status", "last_used_at")
    list_filter = ("status", "tenant")
    search_fields = ("name", "public_id", "client_id", "tenant__name")
