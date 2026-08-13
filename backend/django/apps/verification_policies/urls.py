from common.public_api import internal_api_path, public_api_path

from apps.verification_policies.views import (
    VerificationPolicyActivateView,
    VerificationPolicyArchiveView,
    VerificationPolicyCloneView,
    VerificationPolicyDetailView,
    VerificationPolicyListCreateView,
)


urlpatterns = [
    public_api_path(
        "",
        VerificationPolicyListCreateView.as_view(),
        methods=("GET", "POST"),
        name="verification-policy-list-create",
    ),
    public_api_path(
        "<str:policy_id>",
        VerificationPolicyDetailView.as_view(),
        methods=("GET",),
        name="verification-policy-detail",
    ),
    internal_api_path(
        "<str:policy_id>/clone",
        VerificationPolicyCloneView.as_view(),
        name="verification-policy-clone",
    ),
    internal_api_path(
        "<str:policy_id>/activate",
        VerificationPolicyActivateView.as_view(),
        name="verification-policy-activate",
    ),
    internal_api_path(
        "<str:policy_id>/archive",
        VerificationPolicyArchiveView.as_view(),
        name="verification-policy-archive",
    ),
]
