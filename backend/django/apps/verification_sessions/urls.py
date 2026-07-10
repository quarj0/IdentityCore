from django.urls import path

from apps.verification_sessions.views import (
    VerificationSessionConsentView,
    VerificationSessionDetailView,
    VerificationSessionDocumentView,
    VerificationSessionLivenessView,
    VerificationSessionSelfieView,
    VerificationSessionStatusView,
    VerificationMobileHandoffCreateView,
    VerificationMobileHandoffRedeemView,
)


urlpatterns = [
    path("mobile-handoff/redeem", VerificationMobileHandoffRedeemView.as_view(), name="verification-mobile-handoff-redeem"),
    path("<str:session_id>", VerificationSessionDetailView.as_view(), name="verification-session-detail"),
    path(
        "<str:session_id>/consent",
        VerificationSessionConsentView.as_view(),
        name="verification-session-consent",
    ),
    path(
        "<str:session_id>/documents",
        VerificationSessionDocumentView.as_view(),
        name="verification-session-documents",
    ),
    path(
        "<str:session_id>/selfies",
        VerificationSessionSelfieView.as_view(),
        name="verification-session-selfies",
    ),
    path(
        "<str:session_id>/liveness",
        VerificationSessionLivenessView.as_view(),
        name="verification-session-liveness",
    ),
    path(
        "<str:session_id>/status",
        VerificationSessionStatusView.as_view(),
        name="verification-session-status",
    ),
    path(
        "<str:session_id>/mobile-handoff",
        VerificationMobileHandoffCreateView.as_view(),
        name="verification-mobile-handoff-create",
    ),
]
