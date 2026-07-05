import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "unsafe-development-secret-key-for-identitycore"
)
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.audit.apps.AuditConfig",
    "apps.biometrics.apps.BiometricsConfig",
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.access_control.apps.AccessControlConfig",
    "apps.api_clients.apps.ApiClientsConfig",
    "apps.consent.apps.ConsentConfig",
    "apps.document_captures.apps.DocumentCapturesConfig",
    "apps.identity_documents.apps.IdentityDocumentsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.organizations.apps.OrganizationsConfig",
    "apps.providers.apps.ProvidersConfig",
    "apps.risk.apps.RiskConfig",
    "apps.tenants.apps.TenantsConfig",
    "apps.uploads.apps.UploadsConfig",
    "apps.verification_policies.apps.VerificationPoliciesConfig",
    "apps.verification_sessions.apps.VerificationSessionsConfig",
    "apps.verification_subjects.apps.VerificationSubjectsConfig",
    "apps.verifications.apps.VerificationsConfig",
    "apps.webhooks.apps.WebhooksConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

if (
    os.getenv("POSTGRES_DB")
    and os.getenv("POSTGRES_USER")
    and os.getenv("POSTGRES_HOST")
):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "identitycore"),
            "USER": os.getenv("POSTGRES_USER", "identitycore"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "identitycore"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@identitycore.local")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.PlatformUser"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_DEFAULT_ROUTING_KEY = "default"
CELERY_TASK_ROUTES = {
    "apps.biometrics.tasks.process_verification_biometrics_task": {
        "queue": "ai_processing"
    },
    "apps.identity_documents.tasks.process_identity_document_task": {
        "queue": "ai_processing"
    },
    "apps.uploads.tasks.cleanup_expired_uploads_task": {"queue": "retention"},
    "apps.verifications.tasks.expire_pending_verifications_task": {
        "queue": "retention"
    },
    "apps.verifications.tasks.cleanup_expired_verification_sessions_task": {
        "queue": "retention"
    },
    "apps.verifications.tasks.cleanup_retained_media_task": {"queue": "retention"},
    "apps.webhooks.tasks.process_pending_webhook_events_task": {"queue": "webhooks"},
    "apps.webhooks.tasks.deliver_webhook_event_task": {"queue": "webhooks"},
    "apps.notifications.tasks.process_pending_notifications_task": {
        "queue": "notifications"
    },
    "apps.notifications.tasks.deliver_notification_task": {"queue": "notifications"},
}
CELERY_BEAT_SCHEDULE = {
    "process-pending-webhooks": {
        "task": "apps.webhooks.tasks.process_pending_webhook_events_task",
        "schedule": int(os.getenv("CELERY_WEBHOOK_BEAT_SECONDS", "30")),
        "kwargs": {"limit": int(os.getenv("WEBHOOK_DELIVERY_BATCH_SIZE", "50"))},
    },
    "process-pending-notifications": {
        "task": "apps.notifications.tasks.process_pending_notifications_task",
        "schedule": int(os.getenv("CELERY_NOTIFICATION_BEAT_SECONDS", "30")),
        "kwargs": {"limit": int(os.getenv("NOTIFICATION_DELIVERY_BATCH_SIZE", "50"))},
    },
    "expire-pending-verifications": {
        "task": "apps.verifications.tasks.expire_pending_verifications_task",
        "schedule": int(os.getenv("CELERY_VERIFICATION_EXPIRY_BEAT_SECONDS", "60")),
        "kwargs": {"limit": int(os.getenv("VERIFICATION_EXPIRY_BATCH_SIZE", "100"))},
    },
    "cleanup-expired-verification-sessions": {
        "task": "apps.verifications.tasks.cleanup_expired_verification_sessions_task",
        "schedule": int(os.getenv("CELERY_SESSION_CLEANUP_BEAT_SECONDS", "300")),
        "kwargs": {
            "limit": int(os.getenv("VERIFICATION_SESSION_CLEANUP_BATCH_SIZE", "200"))
        },
    },
    "cleanup-retained-media": {
        "task": "apps.verifications.tasks.cleanup_retained_media_task",
        "schedule": int(os.getenv("CELERY_RETENTION_BEAT_SECONDS", "3600")),
        "kwargs": {"limit": int(os.getenv("RETENTION_CLEANUP_BATCH_SIZE", "100"))},
    },
    "cleanup-expired-uploads": {
        "task": "apps.uploads.tasks.cleanup_expired_uploads_task",
        "schedule": int(os.getenv("CELERY_UPLOAD_CLEANUP_BEAT_SECONDS", "300")),
        "kwargs": {"limit": int(os.getenv("UPLOAD_CLEANUP_BATCH_SIZE", "200"))},
    },
}

AI_SERVICE_BASE_URL = os.getenv("AI_SERVICE_BASE_URL", "http://localhost:8001")
AI_SERVICE_TIMEOUT_SECONDS = int(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "15"))
UPLOAD_URL_BASE = os.getenv("UPLOAD_URL_BASE", "http://localhost:9000/mock-upload")
UPLOAD_URL_EXPIRES_MINUTES = int(os.getenv("UPLOAD_URL_EXPIRES_MINUTES", "10"))
VERIFICATION_PORTAL_BASE_URL = os.getenv(
    "VERIFICATION_PORTAL_BASE_URL", "http://localhost:8000/api/v1/verification-sessions"
)
WEBHOOK_DELIVERY_TIMEOUT_SECONDS = int(
    os.getenv("WEBHOOK_DELIVERY_TIMEOUT_SECONDS", "10")
)
WEBHOOK_MAX_ATTEMPTS = int(os.getenv("WEBHOOK_MAX_ATTEMPTS", "5"))
WEBHOOK_RETRY_BASE_SECONDS = int(os.getenv("WEBHOOK_RETRY_BASE_SECONDS", "60"))
NOTIFICATION_DELIVERY_BATCH_SIZE = int(
    os.getenv("NOTIFICATION_DELIVERY_BATCH_SIZE", "50")
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
}
