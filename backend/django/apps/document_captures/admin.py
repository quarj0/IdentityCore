from django.contrib import admin

from apps.document_captures.models import DocumentCapture


@admin.register(DocumentCapture)
class DocumentCaptureAdmin(admin.ModelAdmin):
    list_display = ("public_id", "identity_document", "side", "status", "captured_at")
    list_filter = ("side", "status", "storage_provider")
    search_fields = ("public_id", "identity_document__public_id", "storage_key")
