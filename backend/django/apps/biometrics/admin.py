from django.contrib import admin

from apps.biometrics.models import SelfieCapture


@admin.register(SelfieCapture)
class SelfieCaptureAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "capture_type", "status", "captured_at")
    list_filter = ("capture_type", "status", "storage_provider")
    search_fields = ("public_id", "verification__public_id", "storage_key")
