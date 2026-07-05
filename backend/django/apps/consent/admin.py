from django.contrib import admin

from apps.consent.models import ConsentRecord, ConsentTemplate


@admin.register(ConsentTemplate)
class ConsentTemplateAdmin(admin.ModelAdmin):
    list_display = ("public_id", "name", "tenant", "version", "language", "status")
    list_filter = ("status", "language")
    search_fields = ("public_id", "name", "tenant__name")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "verification_subject", "accepted_at")
    list_filter = ("accepted",)
    search_fields = (
        "public_id",
        "verification__public_id",
        "verification_subject__public_id",
    )
