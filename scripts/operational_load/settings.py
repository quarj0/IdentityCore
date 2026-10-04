"""Only the dedicated synthetic load environment imports these settings."""

from config.settings.base import *  # noqa: F401,F403
import os

if (
    os.getenv("IDENTITYCORE_SYNTHETIC_LOAD") != "1"
    or os.getenv("POSTGRES_DB") != "identitycore_load"
):
    raise RuntimeError("Load settings require the dedicated synthetic database.")
ADMIN_MFA_REQUIRED_DEFAULT = False
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "api_client": "10000/min",
        "verification_session": "10000/min",
        "dashboard_user": "10000/min",
        "sensitive_public": "10000/min",
    },
}
# Measured workload quotas are explicit fixture settings, not production defaults.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6388/5",
    }
}

MIDDLEWARE = ["operational_load.profiling.LoadProfileMiddleware", *MIDDLEWARE]  # noqa: F405
