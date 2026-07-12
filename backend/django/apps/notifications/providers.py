from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone
from django.utils.module_loading import import_string

from apps.notifications.models import Notification, NotificationChannel
from apps.platform_settings.services import get_platform_setting_value
from apps.providers.models import Provider, ProviderStatus, ProviderType
from apps.providers.services import get_notification_provider_assignment


class NotificationDeliveryError(Exception):
    pass


class NotificationProviderNotConfigured(NotificationDeliveryError):
    pass


@dataclass
class NotificationDeliveryResult:
    provider_reference: str
    sent_at: object


class BaseNotificationProvider:
    def __init__(self, *, provider_code: str, configuration: dict | None = None):
        self.provider_code = provider_code
        self.configuration = configuration or {}

    def deliver(self, notification: Notification) -> NotificationDeliveryResult:
        raise NotImplementedError


class DjangoEmailNotificationProvider(BaseNotificationProvider):
    def _build_connection(self):
        backend = self.configuration.get("email_backend") or getattr(
            settings, "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
        )
        backend_options = dict(self.configuration.get("backend_options") or {})

        if self.configuration.get("backend") == "smtp":
            backend = "django.core.mail.backends.smtp.EmailBackend"
            backend_options.update(
                {
                    "host": self.configuration.get(
                        "host", getattr(settings, "EMAIL_HOST", "")
                    ),
                    "port": int(
                        self.configuration.get(
                            "port", getattr(settings, "EMAIL_PORT", 587)
                        )
                    ),
                    "username": self.configuration.get(
                        "username", getattr(settings, "EMAIL_HOST_USER", "")
                    ),
                    "password": self.configuration.get(
                        "password", getattr(settings, "EMAIL_HOST_PASSWORD", "")
                    ),
                    "use_tls": bool(
                        self.configuration.get(
                            "use_tls", getattr(settings, "EMAIL_USE_TLS", False)
                        )
                    ),
                    "use_ssl": bool(
                        self.configuration.get(
                            "use_ssl", getattr(settings, "EMAIL_USE_SSL", False)
                        )
                    ),
                    "timeout": int(
                        self.configuration.get(
                            "timeout",
                            getattr(settings, "EMAIL_TIMEOUT", 10) or 10,
                        )
                    ),
                }
            )

        return get_connection(backend=backend, fail_silently=False, **backend_options)

    def deliver(self, notification: Notification) -> NotificationDeliveryResult:
        connection = self._build_connection()
        from_email = self.configuration.get("from_email") or str(
            get_platform_setting_value(
                "notifications.default_from_email",
                getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@identitycore.local"),
            )
        )
        message = EmailMultiAlternatives(
            subject=notification.subject or "IdentityCore notification",
            body=notification.body_preview,
            from_email=from_email,
            to=[notification.recipient],
            connection=connection,
        )
        html_body = self.configuration.get("html_body")
        if html_body:
            message.attach_alternative(html_body, "text/html")

        sent_count = message.send(fail_silently=False)
        if sent_count != 1:
            raise NotificationDeliveryError(
                "Email delivery did not report a successful recipient send."
            )

        return NotificationDeliveryResult(
            provider_reference=f"{self.provider_code}:{notification.public_id}",
            sent_at=timezone.now(),
        )


class SMSNotificationProvider(BaseNotificationProvider):
    def deliver(self, notification: Notification) -> NotificationDeliveryResult:
        adapter_path = self.configuration.get("adapter")
        if adapter_path:
            adapter_class = import_string(adapter_path)
            adapter = adapter_class(
                provider_code=self.provider_code,
                configuration=self.configuration,
            )
            return adapter.deliver(notification)
        raise NotificationProviderNotConfigured(
            "SMS delivery is scaffolded but no SMS adapter has been configured yet."
        )


class InAppNotificationProvider(BaseNotificationProvider):
    def deliver(self, notification: Notification) -> NotificationDeliveryResult:
        return NotificationDeliveryResult(
            provider_reference=f"{self.provider_code}:{notification.public_id}",
            sent_at=timezone.now(),
        )


def _get_active_provider_configuration(channel: str) -> tuple[str, dict]:
    for provider in Provider.objects.filter(
        provider_type=ProviderType.NOTIFICATION,
        status=ProviderStatus.ACTIVE,
    ).order_by("name"):
        configuration = provider.configuration_json or {}
        if configuration.get("channel") == channel:
            return provider.code, configuration
    return "", {}


def get_notification_provider(notification: Notification) -> BaseNotificationProvider:
    assignment = get_notification_provider_assignment(notification.tenant, notification.channel)
    if assignment is not None:
        provider_code = assignment.provider.code
        configuration = assignment.provider.configuration_json or {}
    else:
        provider_code, configuration = _get_active_provider_configuration(
            notification.channel
        )

    if notification.channel == NotificationChannel.EMAIL:
        if not provider_code:
            provider_code = str(
                get_platform_setting_value(
                    "notifications.email_provider_code",
                    getattr(settings, "NOTIFICATION_EMAIL_PROVIDER_CODE", "default-email"),
                )
            )
            configuration = {
                "backend": getattr(settings, "NOTIFICATION_EMAIL_PROVIDER", "django")
            }
        return DjangoEmailNotificationProvider(
            provider_code=provider_code,
            configuration=configuration,
        )

    if notification.channel == NotificationChannel.SMS:
        if not provider_code:
            provider_code = str(
                get_platform_setting_value(
                    "notifications.sms_provider_code",
                    getattr(settings, "NOTIFICATION_SMS_PROVIDER_CODE", "default-sms"),
                )
            )
            configuration = {
                "backend": getattr(settings, "NOTIFICATION_SMS_PROVIDER", "stub")
            }
        return SMSNotificationProvider(
            provider_code=provider_code,
            configuration=configuration,
        )

    if notification.channel == NotificationChannel.IN_APP:
        return InAppNotificationProvider(
            provider_code=provider_code or "in-app",
            configuration=configuration,
        )

    raise NotificationProviderNotConfigured(
        f"No notification provider is available for channel '{notification.channel}'."
    )
