from django.urls import path

from apps.verification_policies.views import VerificationPolicyListCreateView


urlpatterns = [
    path("", VerificationPolicyListCreateView.as_view(), name="verification-policy-list-create"),
]
