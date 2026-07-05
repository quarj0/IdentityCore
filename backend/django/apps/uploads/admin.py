from django.contrib import admin

from apps.uploads.models import Upload


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "tenant",
        "purpose",
        "status",
        "mime_type",
        "file_size_bytes",
        "expires_at",
        "consumed_at",
    )
    list_filter = ("purpose", "status", "storage_provider")
    search_fields = ("public_id", "storage_key", "verification__public_id")
    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "deleted_at",
        "consumed_at",
    )
