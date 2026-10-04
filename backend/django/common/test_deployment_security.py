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
