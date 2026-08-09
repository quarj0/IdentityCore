from .base import *  # noqa: F401,F403


DEBUG = False
SECRET_KEY = "test-secret-key-with-at-least-thirty-two-bytes"
# Most legacy integration fixtures authenticate platform administrators directly.
# Individual MFA tests explicitly enable the production default when exercising it.
ADMIN_MFA_REQUIRED_DEFAULT = False
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY  # noqa: F405
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["sensitive_public"] = "10000/min"  # noqa: F405

# Deterministic URL bases keep unit tests independent from external object storage.
UPLOAD_URL_BASE = "http://testserver/uploads"
MEDIA_DOWNLOAD_URL_BASE = "http://testserver/media"
PUBLIC_ASSET_URL_BASE = "http://testserver/assets"
