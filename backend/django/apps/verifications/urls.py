from django.urls import path

from apps.verifications.views import (
    ManualReviewDecisionView,
    ManualReviewListView,
    VerificationCancelView,
    VerificationDetailView,
    VerificationEvidenceReportDownloadView,
    VerificationEvidenceReportPDFDownloadView,
    VerificationEvidenceReportView,
    VerificationListCreateView,
    VerificationResendLinkView,
)


urlpatterns = [
    path("manual-reviews", ManualReviewListView.as_view(), name="manual-review-list"),
    path(
        "manual-reviews/<str:verification_id>/decision",
        ManualReviewDecisionView.as_view(),
        name="manual-review-decision",
    ),
    path("", VerificationListCreateView.as_view(), name="verification-list-create"),
    path("<str:verification_id>", VerificationDetailView.as_view(), name="verification-detail"),
    path(
        "<str:verification_id>/evidence-report",
        VerificationEvidenceReportView.as_view(),
        name="verification-evidence-report",
    ),
    path(
        "<str:verification_id>/evidence-report/download",
        VerificationEvidenceReportDownloadView.as_view(),
        name="verification-evidence-report-download",
    ),
    path(
        "<str:verification_id>/evidence-report/download.pdf",
        VerificationEvidenceReportPDFDownloadView.as_view(),
        name="verification-evidence-report-pdf-download",
    ),
    path("<str:verification_id>/cancel", VerificationCancelView.as_view(), name="verification-cancel"),
    path(
        "<str:verification_id>/resend-link",
        VerificationResendLinkView.as_view(),
        name="verification-resend-link",
    ),
]
