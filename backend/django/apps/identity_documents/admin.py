from django.contrib import admin

from apps.identity_documents.models import IdentityDocument


@admin.register(IdentityDocument)
class IdentityDocumentAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "document_type_id", "status", "created_at")
    list_filter = ("status", "document_type_id")
    search_fields = ("public_id", "verification__public_id", "verification_subject__public_id")
