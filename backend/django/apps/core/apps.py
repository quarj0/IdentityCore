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

        from common.observability import configure
        import os

        name = os.getenv("IDENTITYCORE_SERVICE_NAME", "identitycore-api")
        configure(
            name
            if name
            in {"identitycore-api", "identitycore-worker", "identitycore-operations"}
            else "identitycore-api"
        )
