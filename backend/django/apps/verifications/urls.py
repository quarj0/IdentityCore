from django.urls import path

from apps.verifications.views import VerificationCancelView, VerificationDetailView, VerificationListCreateView


urlpatterns = [
    path("", VerificationListCreateView.as_view(), name="verification-list-create"),
    path("<str:verification_id>", VerificationDetailView.as_view(), name="verification-detail"),
    path("<str:verification_id>/cancel", VerificationCancelView.as_view(), name="verification-cancel"),
]
