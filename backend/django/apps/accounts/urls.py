from django.urls import path

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
    path("login", LoginView.as_view(), name="auth-login"),
    path("refresh", RefreshView.as_view(), name="auth-refresh"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
    path("mfa/enroll", MFAEnrollView.as_view(), name="auth-mfa-enroll"),
    path(
        "mfa/enroll/confirm",
        MFAEnrollConfirmView.as_view(),
        name="auth-mfa-enroll-confirm",
    ),
    path("mfa/challenge", MFAChallengeView.as_view(), name="auth-mfa-challenge"),
    path("mfa/reset", MFAResetView.as_view(), name="auth-mfa-reset"),
    path("me", MeView.as_view(), name="auth-me"),
    path("team", TeamListView.as_view(), name="auth-team"),
    path("team/invitations", TeamInvitationListCreateView.as_view()),
    path("team/invitations/accept", TeamInvitationAcceptView.as_view()),
    path(
        "team/invitations/<str:invitation_id>/<str:action>",
        TeamInvitationActionView.as_view(),
    ),
    path("notification-preferences", NotificationPreferencesView.as_view()),
]
