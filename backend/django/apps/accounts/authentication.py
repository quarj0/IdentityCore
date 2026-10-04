from datetime import timedelta

from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.accounts.models import DashboardSession
from apps.accounts.sessions import _validate_user


class DashboardJWTAuthentication(JWTAuthentication):
    """The same session validity checks apply at REST and GraphQL boundaries."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        try:
            _validate_user(user, validated_token)
        except TokenError as exc:
            raise InvalidToken("Session is no longer valid.") from exc
        session_id = validated_token.get("session_id")
        if session_id:
            now = timezone.now()
            session = DashboardSession.objects.filter(
                user=user,
                public_id=session_id,
                revoked_at__isnull=True,
                deleted_at__isnull=True,
                expires_at__gt=now,
            ).first()
            if session is None:
                raise InvalidToken("Session is no longer valid.")
            DashboardSession.objects.filter(
                pk=session.pk, last_seen_at__lt=now - timedelta(minutes=5)
            ).update(last_seen_at=now)
        return user
