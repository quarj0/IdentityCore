from django.contrib import admin

from apps.tenants.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "public_id", "slug", "organization", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "public_id", "slug", "organization__name")


# Register your models here.
