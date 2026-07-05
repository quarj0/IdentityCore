from django.contrib import admin

from apps.verification_policies.models import VerificationPolicy


@admin.register(VerificationPolicy)
class VerificationPolicyAdmin(admin.ModelAdmin):
    list_display = ("public_id", "name", "tenant", "version", "status")
    list_filter = ("status", "required_liveness_level")
    search_fields = ("public_id", "name", "tenant__name")
