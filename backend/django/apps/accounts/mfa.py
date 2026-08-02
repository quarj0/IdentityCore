"""TOTP enrollment, policy, challenge, and recovery-code helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import MFARecoveryCode, PlatformUser
from apps.platform_settings.services import get_platform_setting_value

MFA_TOKEN_SALT = "identitycore.mfa.login.v1"
MFA_TOKEN_MAX_AGE = 300


def is_mfa_required(user: PlatformUser) -> bool:
    if user.is_platform_admin and get_platform_setting_value(
        "security.admin_mfa_required",
        default=settings.ADMIN_MFA_REQUIRED_DEFAULT,
    ):
        return True
    if user.tenant_id is None:
        return False
    configured = user.tenant.organization.settings_json.get("privileged_mfa_roles", [])
    return user.user_roles.filter(
        role__name__in=configured, role__status="active"
    ).exists()


def issue_mfa_token(user: PlatformUser, *, purpose: str) -> str:
    return signing.dumps(
        {
            "uid": user.pk,
            "purpose": purpose,
            "password": user.password,
            "nonce": secrets.token_urlsafe(16),
        },
        salt=MFA_TOKEN_SALT,
        compress=True,
    )


def resolve_mfa_token(token: str, *, purpose: str) -> PlatformUser:
    try:
        payload = signing.loads(token, salt=MFA_TOKEN_SALT, max_age=MFA_TOKEN_MAX_AGE)
        user = PlatformUser.objects.get(pk=payload["uid"], status="active")
    except (signing.BadSignature, KeyError, PlatformUser.DoesNotExist) as exc:
        raise ValueError("MFA transaction is invalid or expired.") from exc
    if payload.get("purpose") != purpose or payload.get("password") != user.password:
        raise ValueError("MFA transaction is invalid or expired.")
    return user


def consume_mfa_token(user: PlatformUser, token: str) -> bool:
    """Atomically make a successful login challenge transaction single-use."""
    digest = hashlib.sha256(token.encode()).hexdigest()
    with transaction.atomic():
        locked = PlatformUser.objects.select_for_update().get(pk=user.pk)
        consumed = locked.mfa_config_json.get("consumed_challenges", [])
        if digest in consumed:
            return False
        locked.mfa_config_json = {
            **locked.mfa_config_json,
            "consumed_challenges": [*consumed[-19:], digest],
        }
        locked.save(update_fields=["mfa_config_json", "updated_at"])
    user.mfa_config_json = locked.mfa_config_json
    return True


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def provisioning_uri(user: PlatformUser, secret: str) -> str:
    label = quote(f"IdentityCore:{user.email}", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer=IdentityCore&algorithm=SHA1&digits=6&period=30"


def totp(secret: str, *, timestamp: int | None = None) -> str:
    counter = (int(time.time()) if timestamp is None else timestamp) // 30
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    digest = hmac.new(
        base64.b32decode(padded, casefold=True),
        struct.pack(">Q", counter),
        hashlib.sha1,
    ).digest()
    offset = digest[-1] & 0x0F
    number = (
        struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    ) % 1_000_000
    return f"{number:06d}"


def verify_totp(secret: str, code: str) -> bool:
    now = int(time.time())
    return (
        len(code) == 6
        and code.isdigit()
        and any(
            hmac.compare_digest(totp(secret, timestamp=now + drift * 30), code)
            for drift in (-1, 0, 1)
        )
    )


def recovery_hash(user: PlatformUser, code: str) -> str:
    normalized = code.replace("-", "").strip().upper()
    return hmac.new(
        str(user.pk).encode(), normalized.encode(), hashlib.sha256
    ).hexdigest()


def enable_mfa(user: PlatformUser, secret: str) -> list[str]:
    codes = [secrets.token_hex(5).upper() for _ in range(10)]
    with transaction.atomic():
        locked = PlatformUser.objects.select_for_update().get(pk=user.pk)
        locked.mfa_config_json = {"totp_secret": secret}
        locked.mfa_enabled = True
        locked.save(update_fields=["mfa_config_json", "mfa_enabled", "updated_at"])
        locked.mfa_recovery_codes.all().delete()
        for code in codes:
            MFARecoveryCode.objects.create(
                user=locked, code_hash=recovery_hash(locked, code)
            )
    user.mfa_config_json = {"totp_secret": secret}
    user.mfa_enabled = True
    return codes


def verify_challenge(user: PlatformUser, code: str) -> str | None:
    secret = user.mfa_config_json.get("totp_secret", "")
    if secret and verify_totp(secret, code.strip()):
        return "totp"
    digest = recovery_hash(user, code)
    with transaction.atomic():
        recovery = (
            MFARecoveryCode.objects.select_for_update()
            .filter(user=user, code_hash=digest, used_at__isnull=True)
            .first()
        )
        if recovery:
            recovery.used_at = timezone.now()
            recovery.save(update_fields=["used_at", "updated_at"])
            return "recovery_code"
    return None
