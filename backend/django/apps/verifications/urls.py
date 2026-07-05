from django.urls import path

from apps.verifications.views import (
    ManualReviewDecisionView,
    ManualReviewListView,
    VerificationCancelView,
    VerificationDetailView,
    VerificationListCreateView,
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
    path("<str:verification_id>/cancel", VerificationCancelView.as_view(), name="verification-cancel"),
]
