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
from django.utils.crypto import salted_hmac

from apps.accounts.models import MFARecoveryCode, PlatformUser
from apps.platform_settings.services import get_platform_setting_value

MFA_TOKEN_SALT = "identitycore.mfa.login.v2"
MFA_TOKEN_MAX_AGE = 300


def is_mfa_required(user: PlatformUser) -> bool:
    if user.mfa_config_json.get("enrollment_required"):
        return True
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


def _password_binding(user: PlatformUser) -> str:
    value = f"{user.pk}|{user.password}|{user.auth_valid_after or ''}"
    return salted_hmac(
        "identitycore.mfa.password-binding.v2", value, algorithm="sha256"
    ).hexdigest()


def prepare_password_login(user: PlatformUser) -> PlatformUser:
    """Caller holds the audit scope lock and an atomic transaction."""
    user = PlatformUser.objects.select_for_update().get(pk=user.pk)
    if (
        user.mfa_enabled
        and not user.mfa_config_json.get("totp_secret")
        and not user.mfa_recovery_codes.filter(used_at__isnull=True).exists()
    ):
        user.mfa_enabled = False
        user.mfa_config_json = {"enrollment_required": True}
        user.save(update_fields=["mfa_enabled", "mfa_config_json", "updated_at"])
    return user


def issue_mfa_token(user: PlatformUser, *, purpose: str) -> str:
    return signing.dumps(
        {
            "uid": user.pk,
            "purpose": purpose,
            "password_binding": _password_binding(user),
            "nonce": secrets.token_urlsafe(16),
        },
        salt=MFA_TOKEN_SALT,
        compress=True,
    )


def resolve_mfa_token(token: str, *, purpose: str) -> PlatformUser:
    try:
        payload = signing.loads(token, salt=MFA_TOKEN_SALT, max_age=MFA_TOKEN_MAX_AGE)
        user = PlatformUser.objects.get(
            pk=payload["uid"], status="active", deleted_at__isnull=True
        )
    except (signing.BadSignature, KeyError, PlatformUser.DoesNotExist) as exc:
        raise ValueError("MFA transaction is invalid or expired.") from exc
    if (
        payload.get("purpose") != purpose
        or not hmac.compare_digest(
            str(payload.get("password_binding", "")), _password_binding(user)
        )
        or (purpose == "enrollment" and user.mfa_enabled)
        or (purpose == "challenge" and not user.mfa_enabled)
    ):
        raise ValueError("MFA transaction is invalid or expired.")
    return user


def _active_consumed(user: PlatformUser):
    now = int(time.time())
    active = []
    for entry in user.mfa_config_json.get("consumed_challenges", []):
        if isinstance(entry, str):
            # Preserve old consumed digests for one complete challenge lifetime.
            active.append({"digest": entry, "expires": now + MFA_TOKEN_MAX_AGE})
        elif (
            isinstance(entry, dict)
            and type(entry.get("expires")) is int
            and entry["expires"] > now
        ):
            active.append(entry)
    return active


def consume_mfa_token(user: PlatformUser, token: str) -> bool:
    """Keep all live consumed proofs rather than evicting usable replay evidence."""
    digest = hashlib.sha256(token.encode()).hexdigest()
    with transaction.atomic():
        locked = PlatformUser.objects.select_for_update().get(pk=user.pk)
        active = _active_consumed(locked)
        if any(entry.get("digest") == digest for entry in active) or len(active) >= 100:
            return False
        locked.mfa_config_json = {
            **locked.mfa_config_json,
            "consumed_challenges": [
                *active,
                {"digest": digest, "expires": int(time.time()) + MFA_TOKEN_MAX_AGE},
            ],
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


def verified_totp_step(
    secret: str, code: str, *, after: int | None = None
) -> int | None:
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    current = int(time.time()) // 30
    for drift in (-1, 0, 1):
        step = current + drift
        if step < 0 or (after is not None and step <= after):
            continue
        if hmac.compare_digest(totp(secret, timestamp=step * 30), code):
            return step
    return None


def verify_totp(secret: str, code: str) -> bool:
    return verified_totp_step(secret, code) is not None


def protect_recovery_digest(
    user_id: int, digest: str, *, pepper: str | None = None
) -> str:
    mac = salted_hmac(
        "identitycore.mfa.recovery-digest.v2",
        f"{user_id}|{digest}",
        secret=settings.MFA_RECOVERY_PEPPER if pepper is None else pepper,
        algorithm="sha256",
    ).hexdigest()
    return "v2$" + mac[:61]


def recovery_hash(user: PlatformUser, code: str, *, pepper: str | None = None) -> str:
    normalized = code.replace("-", "").strip().upper()
    digest = hmac.new(
        str(user.pk).encode(), normalized.encode(), hashlib.sha256
    ).hexdigest()
    return protect_recovery_digest(user.pk, digest, pepper=pepper)


def _upgrade_legacy_recovery_codes(user: PlatformUser):
    for recovery in MFARecoveryCode.objects.filter(user=user).exclude(
        code_hash__startswith="v2$"
    ):
        MFARecoveryCode.objects.filter(
            pk=recovery.pk, code_hash=recovery.code_hash
        ).update(code_hash=protect_recovery_digest(user.pk, recovery.code_hash))


def enable_mfa(
    user: PlatformUser, secret: str, *, accepted_step: int | None = None
) -> list[str]:
    codes = [secrets.token_hex(16).upper() for _ in range(10)]
    with transaction.atomic():
        locked = PlatformUser.objects.select_for_update().get(pk=user.pk)
        if locked.mfa_enabled:
            raise ValueError("MFA enrollment is already complete.")
        pending = locked.mfa_config_json.get("pending_totp_secret")
        if pending and not hmac.compare_digest(pending, secret):
            raise ValueError("MFA enrollment is no longer current.")
        locked.mfa_config_json = {"totp_secret": secret}
        if accepted_step is not None:
            locked.mfa_config_json["last_totp_step"] = accepted_step
        locked.mfa_enabled = True
        locked.save(update_fields=["mfa_config_json", "mfa_enabled", "updated_at"])
        locked.mfa_recovery_codes.all().delete()
        for code in codes:
            MFARecoveryCode.objects.create(
                user=locked, code_hash=recovery_hash(locked, code)
            )
    user.mfa_config_json = locked.mfa_config_json
    user.mfa_enabled = True
    return codes


def verify_challenge(user: PlatformUser, code: str) -> str | None:
    if not isinstance(code, str) or not 0 < len(code) <= 64:
        return None
    with transaction.atomic():
        locked = PlatformUser.objects.select_for_update().get(pk=user.pk)
        if not locked.mfa_enabled or locked.deleted_at is not None:
            return None
        _upgrade_legacy_recovery_codes(locked)
        secret = locked.mfa_config_json.get("totp_secret", "")
        previous = locked.mfa_config_json.get("last_totp_step")
        if type(previous) is not int:
            previous = None
        step = (
            verified_totp_step(secret, code.strip(), after=previous) if secret else None
        )
        if step is not None:
            locked.mfa_config_json = {**locked.mfa_config_json, "last_totp_step": step}
            locked.save(update_fields=["mfa_config_json", "updated_at"])
            user.mfa_config_json = locked.mfa_config_json
            return "totp"
        digests = [recovery_hash(locked, code)]
        digests.extend(
            recovery_hash(locked, code, pepper=key)
            for key in settings.MFA_RECOVERY_PEPPER_FALLBACKS
        )
        recovery = (
            MFARecoveryCode.objects.select_for_update()
            .filter(user=locked, code_hash__in=digests, used_at__isnull=True)
            .first()
        )
        if recovery:
            recovery.used_at = timezone.now()
            recovery.save(update_fields=["used_at", "updated_at"])
            return "recovery_code"
    return None


def verify_login_challenge(user: PlatformUser, token: str, code: str) -> str | None:
    """Consume proof and factor under one user lock; replay never burns another factor."""
    digest = hashlib.sha256(token.encode()).hexdigest()
    with transaction.atomic():
        locked = PlatformUser.objects.select_for_update().get(pk=user.pk)
        try:
            resolved = resolve_mfa_token(token, purpose="challenge")
        except ValueError:
            return None
        if resolved.pk != locked.pk:
            return None
        active = _active_consumed(locked)
        if any(entry.get("digest") == digest for entry in active) or len(active) >= 100:
            return None
        method = verify_challenge(locked, code)
        if method is None:
            return None
        locked.mfa_config_json = {
            **locked.mfa_config_json,
            "consumed_challenges": [
                *active,
                {"digest": digest, "expires": int(time.time()) + MFA_TOKEN_MAX_AGE},
            ],
        }
        locked.save(update_fields=["mfa_config_json", "updated_at"])
        user.mfa_config_json = locked.mfa_config_json
        return method
