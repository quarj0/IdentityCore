import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import RefreshTokenSession


def issue_refresh_token(user) -> RefreshToken:
    refresh = RefreshToken.for_user(user)
    family_id = uuid.uuid4()
    refresh["family_id"] = str(family_id)
    RefreshTokenSession.objects.create(
        user=user, jti=refresh["jti"], family_id=family_id
    )
    return refresh


def _revoke_family(family_id) -> None:
    now = timezone.now()
    sessions = RefreshTokenSession.objects.filter(family_id=family_id)
    sessions.filter(revoked_at__isnull=True).update(revoked_at=now, updated_at=now)
    for session in sessions:
        try:
            # OutstandingToken/BlacklistedToken remains the authority used by
            # SimpleJWT when validating tokens at the API boundary.
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            outstanding = OutstandingToken.objects.filter(jti=session.jti).first()
            if outstanding:
                BlacklistedToken.objects.get_or_create(token=outstanding)
        except TokenError:
            pass


def rotate_refresh_token(raw_token: str) -> tuple[str, str]:
    """Rotate once; replay of any consumed token revokes its entire family."""
    token = RefreshToken(raw_token, verify=False)
    family_id = token.get("family_id")
    jti = token.get("jti")
    if not family_id or not jti:
        raise TokenError("Untracked refresh token")

    reused = False
    result = None
    with transaction.atomic():
        session = (
            RefreshTokenSession.objects.select_for_update().filter(jti=jti).first()
        )
        if session is None or str(session.family_id) != str(family_id):
            raise TokenError("Unknown refresh token")

        if session.consumed_at is not None or session.revoked_at is not None:
            _revoke_family(session.family_id)
            reused = True
        else:
            # Validate signature, expiry and blacklist only after locking the token row.
            token = RefreshToken(raw_token)
            now = timezone.now()
            claimed = RefreshTokenSession.objects.filter(
                pk=session.pk, consumed_at__isnull=True, revoked_at__isnull=True
            ).update(consumed_at=now, updated_at=now)
            if claimed != 1:
                _revoke_family(session.family_id)
                reused = True
            else:
                token.blacklist()
                token.set_jti()
                token.set_exp()
                token.set_iat()
                RefreshTokenSession.objects.create(
                    user=session.user, jti=token["jti"], family_id=session.family_id
                )
                result = (str(token.access_token), str(token))

    if reused:
        raise TokenError("Refresh token reuse detected")
    if result is None:
        raise TokenError("Unable to rotate refresh token")
    return result


@transaction.atomic
def revoke_refresh_token(raw_token: str) -> None:
    token = RefreshToken(raw_token, verify=False)
    session = (
        RefreshTokenSession.objects.select_for_update()
        .filter(jti=token.get("jti"))
        .first()
    )
    if session:
        _revoke_family(session.family_id)
    else:
        RefreshToken(raw_token).blacklist()
