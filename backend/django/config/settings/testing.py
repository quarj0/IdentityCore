from .base import *  # noqa: F401,F403


DEBUG = False
SECRET_KEY = "test-secret-key-with-at-least-thirty-two-bytes"
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",
    }
}
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Deterministic URL bases keep unit tests independent from external object storage.
UPLOAD_URL_BASE = "http://testserver/uploads"
MEDIA_DOWNLOAD_URL_BASE = "http://testserver/media"
PUBLIC_ASSET_URL_BASE = "http://testserver/assets"
