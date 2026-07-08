from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email


PASSWORD_LETTER_RE = re.compile(r"[A-Za-z]")
PASSWORD_DIGIT_RE = re.compile(r"\d")
PASSWORD_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "yahoo.com",
    "ymail.com",
    "rocketmail.com",
    "icloud.com",
    "me.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "pm.me",
    "zoho.com",
    "gmx.com",
    "mail.com",
    "yandex.com",
}

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamailblock.com",
    "sharklasers.com",
    "temp-mail.org",
    "tempmail.com",
    "tempmailo.com",
    "10minutemail.com",
    "10minutemail.net",
    "yopmail.com",
    "dispostable.com",
    "throwawaymail.com",
    "trashmail.com",
    "maildrop.cc",
    "getnada.com",
    "fakeinbox.com",
    "mintemail.com",
}

RESERVED_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "localhost",
}


class StrongPasswordValidator:
    def __init__(self, min_length: int = 8):
        self.min_length = min_length

    def validate(self, password: str, user=None) -> None:
        if len(password) < self.min_length:
            raise ValidationError(
                f"Password must be at least {self.min_length} characters long."
            )
        if not PASSWORD_LETTER_RE.search(password):
            raise ValidationError("Password must include at least one letter.")
        if not PASSWORD_DIGIT_RE.search(password):
            raise ValidationError("Password must include at least one digit.")
        if not PASSWORD_SPECIAL_RE.search(password):
            raise ValidationError(
                "Password must include at least one special character."
            )

    def get_help_text(self) -> str:
        return (
            f"Your password must be at least {self.min_length} characters long and "
            "include letters, digits, and special characters."
        )


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    validate_email(email)
    return email


def validate_business_email(value: str) -> str:
    email = normalize_email(value)
    domain = email.rsplit("@", maxsplit=1)[-1]

    if (
        domain in RESERVED_EMAIL_DOMAINS
        or domain.endswith(".local")
        or domain.endswith(".invalid")
        or domain.endswith(".test")
    ):
        raise ValidationError("Enter a valid business email domain.")
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise ValidationError("Disposable email addresses are not allowed.")
    if domain in PUBLIC_EMAIL_DOMAINS:
        raise ValidationError(
            "Use your organization email address instead."
        )

    return email
