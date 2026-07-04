from django.contrib import admin

from apps.accounts.models import PlatformUser


@admin.register(PlatformUser)
class PlatformUserAdmin(admin.ModelAdmin):
    list_display = ("email", "public_id", "tenant", "status", "is_platform_admin", "mfa_enabled")
    list_filter = ("status", "is_platform_admin", "mfa_enabled", "is_staff")
    search_fields = ("email", "public_id", "first_name", "last_name")
