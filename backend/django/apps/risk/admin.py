from django.contrib import admin

from apps.risk.models import RiskAssessment


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ("public_id", "tenant", "verification", "risk_level", "risk_score", "recommendation")
    list_filter = ("risk_level", "recommendation")
    search_fields = ("public_id", "verification__public_id")
