"""Startup validation for security-sensitive deployment configuration."""

from collections.abc import Mapping

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
LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "django"}


def validate_production_environment(environment: Mapping[str, str]) -> None:
    """Reject missing secrets and development defaults before Django starts."""

    errors: list[str] = []

    def require_secret(name: str, *, minimum_length: int = 32) -> str:
        value = environment.get(name, "").strip()
        normalized = value.lower()
        if not value:
            errors.append(f"{name} is required")
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

    if errors:
        details = "; ".join(errors)
        raise ImproperlyConfigured(f"Unsafe production configuration: {details}.")
