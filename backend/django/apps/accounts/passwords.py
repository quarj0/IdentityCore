from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import PasswordResetToken, PlatformUser
from apps.audit.services import record_audit_event
from apps.notifications.models import NotificationChannel, NotificationRecipientType
from apps.notifications.services import create_notification


PASSWORD_RESET_EXPIRY_HOURS = 2


def hash_password_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def build_password_reset_url(raw_token: str) -> str:
    base_url = settings.ACCOUNT_PASSWORD_RESET_BASE_URL.rstrip("/")
    query = urlencode({"token": raw_token})
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


@transaction.atomic
def issue_password_reset_token(
    *,
    user: PlatformUser,
    expires_in: timedelta | None = None,
) -> tuple[PasswordResetToken, str]:
    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(revoked_at=timezone.now(), updated_at=timezone.now())

    raw_token = secrets.token_urlsafe(32)
    token = PasswordResetToken.objects.create(
        user=user,
        token_hash=hash_password_reset_token(raw_token),
        expires_at=timezone.now()
        + (expires_in or timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)),
    )
    return token, raw_token


def queue_password_reset_notification(*, user: PlatformUser, reset_url: str) -> None:
    if user.tenant is None:
        return
    create_notification(
        tenant=user.tenant,
        recipient_type=NotificationRecipientType.PLATFORM_USER,
        recipient=user.email,
        channel=NotificationChannel.EMAIL,
        template_code="account.password_reset",
        subject="Reset your IdentityCore password",
        body_preview=f"Use this link to reset your IdentityCore password: {reset_url}",
    )


@transaction.atomic
def request_password_reset(*, email: str, request=None) -> bool:
    normalized_email = PlatformUser.objects.normalize_email(email).strip().lower()
    user = PlatformUser.objects.filter(email=normalized_email).first()
    if user is None:
        return False

    _, raw_token = issue_password_reset_token(user=user)
    queue_password_reset_notification(
        user=user,
        reset_url=build_password_reset_url(raw_token),
    )
    if user.tenant is not None:
        record_audit_event(
            tenant=user.tenant,
            actor=user,
            request=request,
            action="user.password_reset_requested",
            target_type="platform_user",
            target_id=user.public_id,
            metadata={"email": user.email},
            sensitive_metadata={"email": user.email},
        )
    return True


@transaction.atomic
def reset_password_with_token(*, token: str, new_password: str, request=None) -> PlatformUser:
    token_hash = hash_password_reset_token(token)
    reset_token = (
        PasswordResetToken.objects.select_related("user", "user__tenant")
        .filter(token_hash=token_hash)
        .first()
    )
    if reset_token is None:
        raise ValueError("Invalid password reset token.")
    if reset_token.revoked_at is not None:
        raise ValueError("This password reset token has been revoked.")
    if reset_token.used_at is not None:
        raise ValueError("This password reset token has already been used.")
    if reset_token.expires_at <= timezone.now():
        raise ValueError("This password reset token has expired.")

    user = reset_token.user
    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    reset_token.used_at = timezone.now()
    reset_token.save(update_fields=["used_at", "updated_at"])
    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
        revoked_at__isnull=True,
    ).exclude(pk=reset_token.pk).update(
        revoked_at=timezone.now(),
        updated_at=timezone.now(),
    )

    if user.tenant is not None:
        record_audit_event(
            tenant=user.tenant,
            actor=user,
            request=request,
            action="user.password_reset_completed",
            target_type="platform_user",
            target_id=user.public_id,
        )
    return user


@transaction.atomic
def change_password(
    *,
    user: PlatformUser,
    current_password: str,
    new_password: str,
    request=None,
) -> PlatformUser:
    if not user.check_password(current_password):
        raise ValidationError("Current password is incorrect.")

    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now(), updated_at=timezone.now())
    if user.tenant is not None:
        record_audit_event(
            tenant=user.tenant,
            actor=user,
            request=request,
            action="user.password_changed",
            target_type="platform_user",
            target_id=user.public_id,
        )
    return user
