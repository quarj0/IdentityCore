from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from common.configuration import validate_production_environment


def production_environment(**overrides: str) -> dict[str, str]:
    environment = {
        "DJANGO_SECRET_KEY": "django-" + "a" * 64,
        "JWT_SIGNING_KEY": "jwt-" + "b" * 64,
        "AI_SERVICE_SHARED_TOKEN": "c" * 64,
        "POSTGRES_DB": "identitycore",
        "POSTGRES_USER": "identitycore_app",
        "POSTGRES_PASSWORD": "d" * 32,
        "POSTGRES_HOST": "database.internal",
        "DJANGO_ALLOWED_HOSTS": "api.identitycore.example.org",
        "DJANGO_DEBUG": "0",
    }
    environment.update(overrides)
    return environment


class ProductionConfigurationTests(SimpleTestCase):
    def test_accepts_explicit_secure_configuration(self):
        validate_production_environment(production_environment())

    def test_rejects_missing_and_placeholder_secrets_without_exposing_values(self):
        environment = production_environment(
            DJANGO_SECRET_KEY="change-me-super-secret",
            JWT_SIGNING_KEY="",
            AI_SERVICE_SHARED_TOKEN="example-token-that-must-never-run-in-production",
        )

        with self.assertRaises(ImproperlyConfigured) as raised:
            validate_production_environment(environment)

        message = str(raised.exception)
        self.assertIn("DJANGO_SECRET_KEY", message)
        self.assertIn("JWT_SIGNING_KEY", message)
        self.assertIn("AI_SERVICE_SHARED_TOKEN", message)
        self.assertNotIn(environment["AI_SERVICE_SHARED_TOKEN"], message)

    def test_rejects_repository_development_secrets(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "DJANGO_SECRET_KEY must not use a placeholder value"
        ):
            validate_production_environment(
                production_environment(
                    DJANGO_SECRET_KEY="unsafe-development-secret-key-for-identitycore"
                )
            )

    def test_rejects_development_database_and_host_defaults(self):
        environment = production_environment(
            POSTGRES_PASSWORD="identitycore",
            DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,django",
            DJANGO_DEBUG="true",
        )

        with self.assertRaises(ImproperlyConfigured) as raised:
            validate_production_environment(environment)

        message = str(raised.exception)
        self.assertIn("POSTGRES_PASSWORD", message)
        self.assertIn("DJANGO_ALLOWED_HOSTS", message)
        self.assertIn("DJANGO_DEBUG", message)

    def test_requires_independent_signing_keys(self):
        shared_key = "e" * 64

        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "JWT_SIGNING_KEY must be different from DJANGO_SECRET_KEY",
        ):
            validate_production_environment(
                production_environment(
                    DJANGO_SECRET_KEY=shared_key,
                    JWT_SIGNING_KEY=shared_key,
                )
            )
