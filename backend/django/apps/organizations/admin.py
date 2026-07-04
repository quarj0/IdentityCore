from django.contrib import admin

from apps.organizations.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "public_id", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "public_id", "slug")

# Register your models here.
