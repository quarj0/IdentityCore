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
)

urlpatterns = [
    path("login", LoginView.as_view(), name="auth-login"),
    path("refresh", RefreshView.as_view(), name="auth-refresh"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
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
