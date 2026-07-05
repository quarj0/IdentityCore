from django.contrib import admin

from apps.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "actor_type", "action", "target_type", "target_id", "created_at")
    list_filter = ("tenant", "actor_type", "action", "target_type")
    search_fields = ("public_id", "actor_id", "target_id", "action")
