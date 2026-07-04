from django.urls import path

from apps.verification_sessions.views import (
    VerificationSessionConsentView,
    VerificationSessionDetailView,
)


urlpatterns = [
    path("<str:session_id>", VerificationSessionDetailView.as_view(), name="verification-session-detail"),
    path(
        "<str:session_id>/consent",
        VerificationSessionConsentView.as_view(),
        name="verification-session-consent",
    ),
]
