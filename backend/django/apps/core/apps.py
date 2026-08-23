from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self) -> None:
        # Install the redaction boundary after Django configures logging but before
        # request/worker code can emit application records.
        from common.safe_logging import install_safe_logging

        install_safe_logging()
