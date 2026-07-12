from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import NamedTuple
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, PlatformUser, PlatformUserStatus
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
)
from apps.notifications.services import create_notification


EMAIL_VERIFICATION_EXPIRY_HOURS = 24


class EmailVerificationResult(NamedTuple):
    user: PlatformUser
    already_verified: bool


def hash_email_verification_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def build_email_verification_url(raw_token: str) -> str:
    base_url = settings.ACCOUNT_EMAIL_VERIFICATION_BASE_URL.rstrip("/")
    query = urlencode({"token": raw_token})
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


@transaction.atomic
def issue_email_verification_token(
    *,
    user: PlatformUser,
    expires_in: timedelta | None = None,
) -> tuple[EmailVerificationToken, str]:
    if user.tenant_id is None:
        raise ValueError("Email verification tokens are only supported for tenant users.")

    EmailVerificationToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(revoked_at=timezone.now(), updated_at=timezone.now())

    raw_token = secrets.token_urlsafe(32)
    token = EmailVerificationToken.objects.create(
        user=user,
        token_hash=hash_email_verification_token(raw_token),
        expires_at=timezone.now()
        + (expires_in or timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)),
    )
    return token, raw_token


def queue_email_verification_notification(
    *,
    user: PlatformUser,
    verification_url: str,
) -> Notification:
    if user.tenant_id is None:
        raise ValueError("Email verification notifications require a tenant user.")
    return create_notification(
        tenant_id=user.tenant_id,
        recipient_type=NotificationRecipientType.PLATFORM_USER,
        recipient=user.email,
        channel=NotificationChannel.EMAIL,
        template_code="account.email_verification",
        subject="Verify your IdentityCore account",
        body_preview=(
            "Verify your email address to activate your IdentityCore account: "
            f"{verification_url}"
        ),
    )


def issue_and_queue_email_verification(*, user: PlatformUser) -> tuple[EmailVerificationToken, str]:
    token, raw_token = issue_email_verification_token(user=user)
    queue_email_verification_notification(
        user=user,
        verification_url=build_email_verification_url(raw_token),
    )
    return token, raw_token


@transaction.atomic
def verify_email_token(raw_token: str) -> PlatformUser:
    return verify_email_token_with_status(raw_token).user


@transaction.atomic
def verify_email_token_with_status(raw_token: str) -> EmailVerificationResult:
    token_hash = hash_email_verification_token(raw_token)
    token = (
        EmailVerificationToken.objects.select_for_update(of=("self",))
        .select_related("user")
        .filter(token_hash=token_hash)
        .first()
    )
    if token is None:
        raise ValueError("Invalid email verification token.")
    if token.revoked_at is not None:
        raise ValueError("This email verification token has been revoked.")
    if token.used_at is not None:
        return EmailVerificationResult(user=token.user, already_verified=True)
    if token.expires_at <= timezone.now():
        raise ValueError("This email verification token has expired.")

    token.used_at = timezone.now()
    token.save(update_fields=["used_at", "updated_at"])
    user = token.user
    if user.status == PlatformUserStatus.INACTIVE:
        user.status = PlatformUserStatus.ACTIVE
        user.save(update_fields=["status", "updated_at"])
    return EmailVerificationResult(user=user, already_verified=False)
