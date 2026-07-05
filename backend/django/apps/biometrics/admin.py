from django.contrib import admin

from apps.biometrics.models import LivenessCheck, SelfieCapture


@admin.register(SelfieCapture)
class SelfieCaptureAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "capture_type", "status", "captured_at")
    list_filter = ("capture_type", "status", "storage_provider")
    search_fields = ("public_id", "verification__public_id", "storage_key")


@admin.register(LivenessCheck)
class LivenessCheckAdmin(admin.ModelAdmin):
    list_display = ("public_id", "verification", "selfie_capture", "liveness_type", "status", "checked_at")
    list_filter = ("liveness_type", "status")
    search_fields = ("public_id", "verification__public_id", "selfie_capture__public_id")
