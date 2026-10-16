from django.test import SimpleTestCase

from apps.providers.health import _safe_error_code


class ProviderHealthErrorCodeTests(SimpleTestCase):
    def test_only_controlled_codes_and_three_ascii_error_status_digits_are_public(self):
        for code in (
            "provider_timeout",
            "provider_signature_invalid",
            "provider_replay_store_unavailable",
            "provider_http_301",
            "provider_http_401",
            "provider_http_503",
            "provider_http_599",
        ):
            with self.subTest(code=code):
                self.assertEqual(_safe_error_code(code), code)
        for code in (
            "provider_customer_ghana_card_1234",
            "provider_http_123456789",
            "provider_http_200",
            "provider_http_600",
            "provider_http_099",
            "provider_http_٤٠١",
            "provider_http_401\\n",
            "private@example.com",
        ):
            with self.subTest(code=code):
                self.assertEqual(_safe_error_code(code), "provider_error")
