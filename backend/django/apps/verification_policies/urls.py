from django.urls import path

from apps.verification_policies.views import (
    VerificationPolicyActivateView, VerificationPolicyArchiveView,
    VerificationPolicyCloneView, VerificationPolicyDetailView,
    VerificationPolicyListCreateView,
)


urlpatterns = [
    path("", VerificationPolicyListCreateView.as_view(), name="verification-policy-list-create"),
    path("<str:policy_id>", VerificationPolicyDetailView.as_view(), name="verification-policy-detail"),
    path("<str:policy_id>/clone", VerificationPolicyCloneView.as_view(), name="verification-policy-clone"),
    path("<str:policy_id>/activate", VerificationPolicyActivateView.as_view(), name="verification-policy-activate"),
    path("<str:policy_id>/archive", VerificationPolicyArchiveView.as_view(), name="verification-policy-archive"),
]
