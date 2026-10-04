"""Owned browser sessions, immediate revocation and replay-safe rotation."""

import hashlib
import hmac
import ipaddress
import uuid
from datetime import datetime, timedelta, timezone as utc_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError, TokenBackendError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.accounts.models import DashboardSession, PlatformUser, RefreshTokenSession


def password_binding(user):
    return hmac.new(
        settings.SECRET_KEY.encode(),
        ("session-password:" + user.password).encode(),
        hashlib.sha256,
    ).hexdigest()


def _expiry(token):
    return datetime.fromtimestamp(token["exp"], tz=utc_timezone.utc)


def _metadata(request):
    if request is None:
        return "legacy", "Unknown device", ""
    scope = request.headers.get("X-IdentityCore-Session-Scope", "legacy")
    if scope not in {"legacy", "dashboard", "platform_admin"}:
        raise TokenError("Invalid session scope")
    agent = request.META.get("HTTP_USER_AGENT", "")[:512]
    browser = next(
        (
            name
            for marker, name in [
                ("Edg/", "Edge"),
                ("Firefox/", "Firefox"),
                ("Chrome/", "Chrome"),
                ("Safari/", "Safari"),
            ]
            if marker in agent
        ),
        "Browser",
    )
    system = next(
        (
            name
            for marker, name in [
                ("Android", "Android"),
                ("iPhone", "iOS"),
                ("iPad", "iOS"),
                ("Windows", "Windows"),
                ("Macintosh", "macOS"),
                ("Linux", "Linux"),
            ]
            if marker in agent
        ),
        "unknown system",
    )
    try:
        peer = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))
        network = str(
            ipaddress.ip_network(
                f"{peer}/{24 if peer.version == 4 else 48}", strict=False
            )
        )
    except ValueError:
        network = ""
    return scope, f"{browser} on {system}", network


def _register(token, user, family):
    OutstandingToken.objects.update_or_create(
        jti=token["jti"],
        defaults={
            "user": user,
            "token": str(token),
            "created_at": timezone.now(),
            "expires_at": _expiry(token),
        },
    )
    RefreshTokenSession.objects.create(
        user=user,
        jti=token["jti"],
        family_id=family.family_id,
        expires_at=_expiry(token),
    )


@transaction.atomic
def issue_refresh_token(user, *, request=None, mfa_verified=False) -> RefreshToken:
    user = PlatformUser.objects.select_for_update().get(pk=user.pk)
    _validate_user(user)
    refresh = RefreshToken.for_user(user)
    scope, label, network = _metadata(request)
    family = DashboardSession.objects.create(
        user=user,
        scope=scope,
        device_label=label,
        peer_network=network,
        last_seen_at=timezone.now(),
        expires_at=_expiry(refresh),
    )
    refresh["family_id"] = str(family.family_id)
    refresh["session_id"] = family.public_id
    refresh["password_binding"] = password_binding(user)
    refresh["mfa_verified"] = bool(mfa_verified)
    _register(refresh, user, family)
    return refresh


def _validate_user(user, token=None):
    from apps.accounts.mfa import is_mfa_required

    if not user.is_active or user.deleted_at is not None:
        raise TokenError("Inactive account")
    if user.tenant_id is not None and (
        user.tenant.deleted_at is not None
        or user.tenant.status in {"suspended", "closed"}
    ):
        raise TokenError("Inactive organization")
    if token is None:
        return
    binding = token.get("password_binding")
    if binding is not None and not hmac.compare_digest(
        str(binding), password_binding(user)
    ):
        raise TokenError("Credentials changed")
    if (
        binding is None
        and user.auth_valid_after is not None
        and token.get("iat", 0) <= user.auth_valid_after.timestamp()
    ):
        raise TokenError("Legacy credentials invalidated")
    if (is_mfa_required(user) or user.mfa_enabled) and token.get(
        "mfa_verified"
    ) is not True:
        raise TokenError("MFA is required")


def _revoke_family(family_id):
    now = timezone.now()
    DashboardSession.objects.filter(family_id=family_id).update(
        revoked_at=now, updated_at=now
    )
    rows = RefreshTokenSession.objects.filter(family_id=family_id)
    rows.filter(revoked_at__isnull=True).update(revoked_at=now, updated_at=now)
    live = OutstandingToken.objects.filter(
        jti__in=rows.values("jti"), expires_at__gt=now, blacklistedtoken__isnull=True
    )
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in live], ignore_conflicts=True
    )


def _decode_refresh(raw_token):
    # Verify signature and expiry even for consumed tokens before revoking a
    # family. Blacklist validation follows identification of a signed replay.
    try:
        payload = token_backend.decode(raw_token, verify=True)
    except TokenBackendError as exc:
        raise TokenError("Invalid refresh token") from exc
    if payload.get("token_type") != "refresh":
        raise TokenError("Invalid token type")
    return RefreshToken(raw_token, verify=False)


def rotate_refresh_token(raw_token: str, *, request=None) -> tuple[str, str]:
    token = _decode_refresh(raw_token)
    reused = False
    result = None
    with transaction.atomic():
        user = (
            PlatformUser.objects.select_for_update()
            .filter(pk=token.get("user_id"))
            .first()
        )
        if user is None:
            raise TokenError("Unknown account")
        _validate_user(user, token)
        row = (
            RefreshTokenSession.objects.select_for_update()
            .filter(jti=token["jti"], user=user)
            .first()
        )
        try:
            family_id = (
                uuid.UUID(str(token.get("family_id")))
                if token.get("family_id")
                else (row.family_id if row else uuid.uuid4())
            )
        except ValueError as exc:
            raise TokenError("Invalid family") from exc
        if row is None and token.get("family_id"):
            raise TokenError("Unknown refresh token")
        if row and row.family_id != family_id:
            raise TokenError("Invalid family")
        scope, label, network = _metadata(request)
        family, _ = DashboardSession.objects.get_or_create(
            family_id=family_id,
            defaults={
                "user": user,
                "scope": scope,
                "device_label": label,
                "peer_network": network,
                "last_seen_at": timezone.now(),
                "expires_at": _expiry(token),
            },
        )
        if (
            family.user_id != user.pk
            or family.revoked_at is not None
            or family.expires_at <= timezone.now()
        ):
            raise TokenError("Session revoked or expired")
        if (
            request is not None
            and scope != "legacy"
            and family.scope not in {scope, "legacy"}
        ):
            raise TokenError("Wrong session scope")
        if row and (row.consumed_at is not None or row.revoked_at is not None):
            _revoke_family(family_id)
            PlatformUser.objects.filter(pk=user.pk).update(auth_valid_after=timezone.now())
            reused = True
        else:
            RefreshToken(raw_token)
            if row is None:
                row = RefreshTokenSession.objects.create(
                    user=user,
                    jti=token["jti"],
                    family_id=family_id,
                    expires_at=_expiry(token),
                )
            now = timezone.now()
            row.consumed_at = now
            row.save(update_fields=["consumed_at", "updated_at"])
            token.blacklist()
            token.set_jti()
            token.set_exp()
            token.set_iat()
            token["family_id"] = str(family_id)
            token["session_id"] = family.public_id
            token["password_binding"] = password_binding(user)
            family.last_seen_at = now
            family.expires_at = _expiry(token)
            if family.scope == "legacy" and scope != "legacy":
                family.scope = scope
            family.save(
                update_fields=["last_seen_at", "expires_at", "scope", "updated_at"]
            )
            _register(token, user, family)
            result = (str(token.access_token), str(token))
    if reused:
        raise TokenError("Refresh token reuse detected")
    return result


@transaction.atomic
def revoke_refresh_token(raw_token: str):
    token = _decode_refresh(raw_token)
    user = (
        PlatformUser.objects.select_for_update().filter(pk=token.get("user_id")).first()
    )
    if user is None:
        raise TokenError("Unknown account")
    row = RefreshTokenSession.objects.filter(jti=token["jti"], user=user).first()
    if row:
        _revoke_family(row.family_id)
    else:
        RefreshToken(raw_token).blacklist()
    PlatformUser.objects.filter(pk=user.pk).update(auth_valid_after=timezone.now())


@transaction.atomic
def revoke_user_sessions(user, *, except_session_id=None):
    user = PlatformUser.objects.select_for_update().get(pk=user.pk)
    families = DashboardSession.objects.filter(user=user, revoked_at__isnull=True)
    if except_session_id:
        families = families.exclude(public_id=except_session_id)
    for family in families:
        _revoke_family(family.family_id)
    known = DashboardSession.objects.filter(user=user).values("family_id")
    for family_id in (
        RefreshTokenSession.objects.filter(user=user, revoked_at__isnull=True)
        .exclude(family_id__in=known)
        .values_list("family_id", flat=True)
        .distinct()
    ):
        _revoke_family(family_id)
    PlatformUser.objects.filter(pk=user.pk).update(auth_valid_after=timezone.now())


def purge_expired_session_history(*, limit=1000):
    now = timezone.now()
    ids = list(
        RefreshTokenSession.objects.filter(expires_at__lt=now)
        .order_by("expires_at")
        .values_list("pk", flat=True)[:limit]
    )
    removed, _ = RefreshTokenSession.objects.filter(pk__in=ids).delete()
    ids = list(
        DashboardSession.objects.filter(expires_at__lt=now - timedelta(days=90))
        .order_by("expires_at")
        .values_list("pk", flat=True)[:limit]
    )
    removed += DashboardSession.objects.filter(pk__in=ids).delete()[0]
    ids = list(OutstandingToken.objects.filter(expires_at__lt=now).order_by("expires_at").values_list("pk", flat=True)[:limit])
    return removed + OutstandingToken.objects.filter(pk__in=ids).delete()[0]
