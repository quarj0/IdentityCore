from django.urls import path

from apps.risk.views import RiskAssessmentListView


urlpatterns = [
    path("", RiskAssessmentListView.as_view(), name="risk-assessment-list"),
]
