from django.contrib import admin

from apps.verifications.models import Verification, VerificationDecision, VerificationSession


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "status", "external_reference", "created_at", "expires_at")
    list_filter = ("tenant", "status")
    search_fields = ("public_id", "external_reference", "purpose")


@admin.register(VerificationSession)
class VerificationSessionAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "tenant", "status", "expires_at", "created_at")
    list_filter = ("tenant", "status")
    search_fields = ("public_id", "verification__public_id")


@admin.register(VerificationDecision)
class VerificationDecisionAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "decision", "decision_type", "decided_at")
    list_filter = ("decision", "decision_type")
    search_fields = ("public_id", "verification__public_id", "reason_code")
