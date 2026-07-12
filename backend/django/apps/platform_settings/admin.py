from django.contrib import admin

from apps.platform_settings.models import PlatformSetting, PlatformSettingRevision


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "group", "title", "status", "is_editable", "updated_at")
    list_filter = ("group", "status", "is_editable", "is_secret")
    search_fields = ("key", "title", "description")


@admin.register(PlatformSettingRevision)
class PlatformSettingRevisionAdmin(admin.ModelAdmin):
    list_display = ("setting", "changed_by", "change_reason", "created_at")
    search_fields = ("setting__key", "change_reason")
