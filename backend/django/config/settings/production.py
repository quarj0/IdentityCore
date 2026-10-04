import os

from common.configuration import validate_production_environment

from .base import *  # noqa: F401,F403

DEBUG = False

# Validate the raw environment rather than settings defaults: production must never
# silently inherit credentials intended only for local development.
validate_production_environment(os.environ)

# TLS terminators must strip client forwarding headers before setting this header.
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
X_FRAME_OPTIONS = "DENY"
if os.getenv("DJANGO_TRUST_PROXY_HEADERS", "").lower() in {"1", "true"}:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Production never inherits local browser allowlists from base settings.
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
AUTH_REFRESH_COOKIE_SECURE = True
