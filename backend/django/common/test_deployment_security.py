from django.test import SimpleTestCase, override_settings
from common.cors import is_allowed_local_origin


class ProductionCorsTests(SimpleTestCase):
    @override_settings(
        DEBUG=False, CORS_ALLOWED_ORIGINS=["https://dashboard.example.org"]
    )
    def test_production_requires_exact_explicit_origin(self):
        self.assertTrue(is_allowed_local_origin("https://dashboard.example.org"))
        for origin in [
            "https://localhost",
            "http://127.0.0.1",
            "null",
            "https://dashboard.example.org.evil.invalid",
        ]:
            self.assertFalse(is_allowed_local_origin(origin))

    @override_settings(DEBUG=True, CORS_ALLOWED_ORIGINS=[])
    def test_development_retains_local_origin_support(self):
        self.assertTrue(is_allowed_local_origin("http://localhost:3000"))

    def test_production_configuration_rejects_unscoped_browser_origins(self):
        from common.configuration import validate_production_environment
        from common.test_configuration import production_environment
        from django.core.exceptions import ImproperlyConfigured

        for value in [
            "http://dashboard.example.org",
            "https://localhost",
            "https://*.example.org",
            "https://dashboard.example.org/path",
            "https://user:private@dashboard.example.org",
        ]:
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                validate_production_environment(
                    production_environment(DJANGO_CORS_ALLOWED_ORIGINS=value)
                )
        validate_production_environment(
            production_environment(
                DJANGO_CORS_ALLOWED_ORIGINS="https://dashboard.example.org",
                DJANGO_CSRF_TRUSTED_ORIGINS="https://dashboard.example.org",
            )
        )

    def test_production_settings_remove_default_local_allowlists(self):
        import runpy
        from unittest.mock import patch
        from common.test_configuration import production_environment

        with patch.dict("os.environ", production_environment(), clear=True):
            config = runpy.run_module("config.settings.production")
        self.assertEqual(config["CORS_ALLOWED_ORIGINS"], [])
        self.assertEqual(config["CSRF_TRUSTED_ORIGINS"], [])
        self.assertTrue(config["AUTH_REFRESH_COOKIE_SECURE"])
        self.assertTrue(config["SECURE_SSL_REDIRECT"])
        self.assertGreaterEqual(config["SECURE_HSTS_SECONDS"], 31536000)
