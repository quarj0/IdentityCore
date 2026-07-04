from django.contrib import admin

from apps.verification_subjects.models import VerificationSubject


@admin.register(VerificationSubject)
class VerificationSubjectAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "external_reference", "full_name", "email", "phone_number")
    list_filter = ("tenant",)
    search_fields = ("public_id", "external_reference", "full_name", "email", "phone_number")
