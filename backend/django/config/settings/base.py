import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parents[2]


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def env_one_of(name: str, fallback_names: list[str], default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    for fallback in fallback_names:
        value = os.getenv(fallback)
        if value:
            return value
    return default


LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:3004",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "unsafe-development-secret-key-for-identitycore"
)
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS", ",".join(LOCAL_FRONTEND_ORIGINS)
)
CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS", ",".join(LOCAL_FRONTEND_ORIGINS)
)
CORS_ALLOW_HEADERS = env_list(
    "DJANGO_CORS_ALLOW_HEADERS",
    "Accept,Authorization,Content-Type,X-Requested-With,X-Session-Id,X-Device-Fingerprint,X-Request-Id",
)
CORS_ALLOW_METHODS = env_list(
    "DJANGO_CORS_ALLOW_METHODS",
    "GET,POST,PUT,PATCH,DELETE,OPTIONS",
)
CORS_PREFLIGHT_MAX_AGE = int(os.getenv("DJANGO_CORS_PREFLIGHT_MAX_AGE", "86400"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.audit.apps.AuditConfig",
    "apps.biometrics.apps.BiometricsConfig",
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.access_control.apps.AccessControlConfig",
    "apps.api_clients.apps.ApiClientsConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.billing.apps.BillingConfig",
    "apps.consent.apps.ConsentConfig",
    "apps.document_captures.apps.DocumentCapturesConfig",
    "apps.feature_flags.apps.FeatureFlagsConfig",
    "apps.identity_documents.apps.IdentityDocumentsConfig",
    "apps.incidents.apps.IncidentsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.organizations.apps.OrganizationsConfig",
    "apps.providers.apps.ProvidersConfig",
    "apps.platform_settings.apps.PlatformSettingsConfig",
    "apps.projects.apps.ProjectsConfig",
    "apps.risk.apps.RiskConfig",
    "apps.reviewers.apps.ReviewersConfig",
    "apps.security.apps.SecurityConfig",
    "apps.support.apps.SupportConfig",
    "apps.templates.apps.TemplatesConfig",
    "apps.tenants.apps.TenantsConfig",
    "apps.uploads.apps.UploadsConfig",
    "apps.verification_policies.apps.VerificationPoliciesConfig",
    "apps.verification_sessions.apps.VerificationSessionsConfig",
    "apps.verification_subjects.apps.VerificationSubjectsConfig",
    "apps.verifications.apps.VerificationsConfig",
    "apps.webhooks.apps.WebhooksConfig",
    "apps.workflows.apps.WorkflowsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "common.cors.LocalCorsMiddleware",
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
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "common.validators.StrongPasswordValidator",
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
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))

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
AI_SERVICE_SHARED_TOKEN = os.getenv("AI_SERVICE_SHARED_TOKEN", "")
UPLOAD_URL_BASE = os.getenv("UPLOAD_URL_BASE", "")
UPLOAD_URL_EXPIRES_MINUTES = int(os.getenv("UPLOAD_URL_EXPIRES_MINUTES", "10"))
MEDIA_DOWNLOAD_URL_BASE = os.getenv("MEDIA_DOWNLOAD_URL_BASE", UPLOAD_URL_BASE)
MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS = int(
    os.getenv("MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS", "300")
)
PUBLIC_ASSET_URL_BASE = os.getenv("PUBLIC_ASSET_URL_BASE", "")
APPLICATION_ENCRYPTION_KEYRING = os.getenv("APPLICATION_ENCRYPTION_KEYRING", "")
APPLICATION_ENCRYPTION_ACTIVE_KEY_ID = os.getenv(
    "APPLICATION_ENCRYPTION_ACTIVE_KEY_ID", ""
)
OBJECT_STORAGE_PROVIDER = env_one_of("OBJECT_STORAGE_PROVIDER", ["R2_PROVIDER"], "")
OBJECT_STORAGE_BUCKET = env_one_of("OBJECT_STORAGE_BUCKET", ["R2_MEDIA_BUCKET"], "")
OBJECT_STORAGE_MEDIA_BUCKET = env_one_of(
    "OBJECT_STORAGE_MEDIA_BUCKET", ["R2_MEDIA_BUCKET"], OBJECT_STORAGE_BUCKET
)
OBJECT_STORAGE_TEMP_BUCKET = env_one_of(
    "OBJECT_STORAGE_TEMP_BUCKET", ["R2_TEMP_BUCKET"], OBJECT_STORAGE_BUCKET
)
OBJECT_STORAGE_EVIDENCE_BUCKET = env_one_of(
    "OBJECT_STORAGE_EVIDENCE_BUCKET", ["R2_EVIDENCE_BUCKET"], ""
)
OBJECT_STORAGE_PUBLIC_BUCKET = env_one_of(
    "OBJECT_STORAGE_PUBLIC_BUCKET", ["R2_PUBLIC_BUCKET"], ""
)
OBJECT_STORAGE_ENDPOINT_URL = config(
    "R2_ENDPOINT_URL", default=os.getenv("OBJECT_STORAGE_ENDPOINT_URL", "")
)
OBJECT_STORAGE_ACCESS_KEY_ID = config(
    "R2_ACCESS_KEY_ID", default=os.getenv("OBJECT_STORAGE_ACCESS_KEY_ID", "")
)
OBJECT_STORAGE_SECRET_ACCESS_KEY = config(
    "R2_SECRET_ACCESS_KEY",
    default=os.getenv("OBJECT_STORAGE_SECRET_ACCESS_KEY", ""),
)
OBJECT_STORAGE_ACCOUNT_ID = config(
    "R2_ACCOUNT_ID", default=os.getenv("OBJECT_STORAGE_ACCOUNT_ID", "")
)

OBJECT_STORAGE_REGION = env_one_of("OBJECT_STORAGE_REGION", ["R2_REGION"], "")
OBJECT_STORAGE_SIGNATURE_VERSION = os.getenv("OBJECT_STORAGE_SIGNATURE_VERSION", "s3v4")
OBJECT_STORAGE_USE_PATH_STYLE = env_bool("OBJECT_STORAGE_USE_PATH_STYLE", False)
OBJECT_STORAGE_ENFORCE_SERVER_SIDE_ENCRYPTION = env_bool(
    "OBJECT_STORAGE_ENFORCE_SERVER_SIDE_ENCRYPTION", True
)
OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION = os.getenv(
    "OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION", "AES256"
)
OBJECT_STORAGE_KMS_KEY_ID = os.getenv("OBJECT_STORAGE_KMS_KEY_ID", "")
OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS = int(
    os.getenv(
        "OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS",
        str(UPLOAD_URL_EXPIRES_MINUTES * 60),
    )
)
APP_MANAGED_MEDIA_ENCRYPTION_ENABLED = env_bool(
    "APP_MANAGED_MEDIA_ENCRYPTION_ENABLED", True
)
VERIFICATION_PORTAL_BASE_URL = os.getenv(
    "VERIFICATION_PORTAL_BASE_URL", "http://localhost:3002/verify"
)
AUTH_REFRESH_COOKIE_NAME = os.getenv("AUTH_REFRESH_COOKIE_NAME", "identitycore_refresh")
AUTH_REFRESH_COOKIE_DOMAIN = os.getenv("AUTH_REFRESH_COOKIE_DOMAIN") or None
AUTH_REFRESH_COOKIE_SECURE = env_bool("AUTH_REFRESH_COOKIE_SECURE", not DEBUG)
AUTH_REFRESH_COOKIE_SAMESITE = os.getenv("AUTH_REFRESH_COOKIE_SAMESITE", "Lax")
AUTH_REFRESH_COOKIE_PATH = "/api/v1/auth/"
ACCOUNT_EMAIL_VERIFICATION_BASE_URL = os.getenv(
    "ACCOUNT_EMAIL_VERIFICATION_BASE_URL",
    "http://localhost:3001/verify-email",
)
ACCOUNT_PASSWORD_RESET_BASE_URL = os.getenv(
    "ACCOUNT_PASSWORD_RESET_BASE_URL",
    "http://localhost:3001/reset-password",
)
WEBHOOK_DELIVERY_TIMEOUT_SECONDS = int(
    os.getenv("WEBHOOK_DELIVERY_TIMEOUT_SECONDS", "10")
)
WEBHOOK_MAX_ATTEMPTS = int(os.getenv("WEBHOOK_MAX_ATTEMPTS", "5"))
WEBHOOK_RETRY_BASE_SECONDS = int(os.getenv("WEBHOOK_RETRY_BASE_SECONDS", "60"))
NOTIFICATION_DELIVERY_BATCH_SIZE = int(
    os.getenv("NOTIFICATION_DELIVERY_BATCH_SIZE", "50")
)
NOTIFICATION_EMAIL_PROVIDER = os.getenv("NOTIFICATION_EMAIL_PROVIDER", "django")
NOTIFICATION_EMAIL_PROVIDER_CODE = os.getenv(
    "NOTIFICATION_EMAIL_PROVIDER_CODE", "default-email"
)
NOTIFICATION_SMS_PROVIDER = os.getenv("NOTIFICATION_SMS_PROVIDER", "stub")
NOTIFICATION_SMS_PROVIDER_CODE = os.getenv(
    "NOTIFICATION_SMS_PROVIDER_CODE", "default-sms"
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "common.throttling.APIClientRateThrottle",
        "common.throttling.VerificationSessionRateThrottle",
        "common.throttling.DashboardUserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "api_client": "100/min",
        "verification_session": "30/min",
        "dashboard_user": "300/min",
    },
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "SIGNING_KEY": env_one_of("JWT_SIGNING_KEY", ["DJANGO_SECRET_KEY"], SECRET_KEY),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
