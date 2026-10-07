"""Startup validation for security-sensitive deployment configuration."""

import hashlib
import json
from collections.abc import Mapping
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

PLACEHOLDER_PARTS = (
    "change-me",
    "changeme",
    "development",
    "example",
    "placeholder",
    "unsafe",
    "<your-",
)
# Fingerprint of the public credential formerly shipped in .env.example.
PUBLIC_AI_TOKEN_FINGERPRINT = (
    "79629f59fda9e6e75efdf001192ee4e9b5409def42acf48eac30b0931bd71c54"
)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "::1", "django"}


def validate_production_environment(environment: Mapping[str, str]) -> None:
    """Reject missing secrets and development defaults before Django starts."""

    errors: list[str] = []

    def require_secret(
        name: str, *, minimum_length: int = 32, value: str | None = None
    ) -> str:
        value = (environment.get(name, "") if value is None else value).strip()
        normalized = value.lower()
        if not value:
            errors.append(f"{name} is required")
        elif (
            name == "AI_SERVICE_SHARED_TOKEN"
            and hashlib.sha256(value.encode()).hexdigest()
            == PUBLIC_AI_TOKEN_FINGERPRINT
        ):
            errors.append(
                f"{name} must not use the formerly published example credential"
            )
        elif normalized in {"identitycore", "password", "secret"} or any(
            marker in normalized for marker in PLACEHOLDER_PARTS
        ):
            errors.append(f"{name} must not use a placeholder value")
        elif len(value) < minimum_length:
            errors.append(f"{name} must contain at least {minimum_length} characters")
        return value

    django_key = require_secret("DJANGO_SECRET_KEY", minimum_length=50)
    jwt_key = require_secret("JWT_SIGNING_KEY", minimum_length=64)
    require_secret("AI_SERVICE_SHARED_TOKEN", minimum_length=32)
    require_secret("POSTGRES_PASSWORD", minimum_length=16)

    if environment.get("MFA_RECOVERY_PEPPER"):
        require_secret("MFA_RECOVERY_PEPPER")
    if environment.get("MFA_RECOVERY_PEPPER_FALLBACKS"):
        try:
            fallbacks = json.loads(environment["MFA_RECOVERY_PEPPER_FALLBACKS"])
        except (TypeError, json.JSONDecodeError):
            fallbacks = None
        if not isinstance(fallbacks, list) or any(
            not isinstance(key, str) for key in fallbacks
        ):
            errors.append(
                "MFA_RECOVERY_PEPPER_FALLBACKS must be a JSON array of secret strings"
            )
        else:
            for key in fallbacks:
                require_secret("MFA_RECOVERY_PEPPER_FALLBACKS", value=key)

    if django_key and jwt_key and django_key == jwt_key:
        errors.append("JWT_SIGNING_KEY must be different from DJANGO_SECRET_KEY")

    required_database_values = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_HOST")
    for name in required_database_values:
        if not environment.get(name, "").strip():
            errors.append(f"{name} is required")

    allowed_hosts = {
        host.strip().lower()
        for host in environment.get("DJANGO_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    }
    if not allowed_hosts:
        errors.append("DJANGO_ALLOWED_HOSTS must list production hostnames")
    elif "*" in allowed_hosts or allowed_hosts <= LOCAL_HOSTS:
        errors.append("DJANGO_ALLOWED_HOSTS must not use wildcard or local-only hosts")

    if environment.get("DJANGO_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        errors.append("DJANGO_DEBUG must be disabled in production")

    for name in ("DJANGO_CORS_ALLOWED_ORIGINS", "DJANGO_CSRF_TRUSTED_ORIGINS"):
        for value in environment.get(name, "").split(","):
            value = value.strip()
            if not value:
                continue
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.hostname in LOCAL_HOSTS
                or "*" in value
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                errors.append(f"{name} must contain explicit HTTPS production origins")
    if errors:
        details = "; ".join(errors)
        raise ImproperlyConfigured(f"Unsafe production configuration: {details}.")
