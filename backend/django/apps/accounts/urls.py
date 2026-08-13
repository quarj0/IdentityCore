from common.public_api import internal_api_path, public_api_path

from apps.accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    NotificationPreferencesView,
    RefreshView,
    TeamInvitationAcceptView,
    TeamInvitationActionView,
    TeamInvitationListCreateView,
    TeamListView,
    MFAChallengeView,
    MFAEnrollConfirmView,
    MFAEnrollView,
    MFAResetView,
)

urlpatterns = [
    public_api_path("login", LoginView.as_view(), methods=("POST",), name="auth-login"),
    public_api_path(
        "refresh", RefreshView.as_view(), methods=("POST",), name="auth-refresh"
    ),
    internal_api_path("logout", LogoutView.as_view(), name="auth-logout"),
    public_api_path(
        "mfa/enroll",
        MFAEnrollView.as_view(),
        methods=("POST",),
        name="auth-mfa-enroll",
    ),
    public_api_path(
        "mfa/enroll/confirm",
        MFAEnrollConfirmView.as_view(),
        methods=("POST",),
        name="auth-mfa-enroll-confirm",
    ),
    public_api_path(
        "mfa/challenge",
        MFAChallengeView.as_view(),
        methods=("POST",),
        name="auth-mfa-challenge",
    ),
    internal_api_path("mfa/reset", MFAResetView.as_view(), name="auth-mfa-reset"),
    public_api_path("me", MeView.as_view(), methods=("GET",), name="auth-me"),
    internal_api_path("team", TeamListView.as_view(), name="auth-team"),
    internal_api_path("team/invitations", TeamInvitationListCreateView.as_view()),
    internal_api_path("team/invitations/accept", TeamInvitationAcceptView.as_view()),
    internal_api_path(
        "team/invitations/<str:invitation_id>/<str:action>",
        TeamInvitationActionView.as_view(),
    ),
    internal_api_path(
        "notification-preferences", NotificationPreferencesView.as_view()
    ),
]
