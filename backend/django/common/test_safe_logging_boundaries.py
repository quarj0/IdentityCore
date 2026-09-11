import io
import logging

from django.test import SimpleTestCase

from common.safe_logging import LOG_FORMAT_ERROR, install_safe_logging


class SafeLoggingBoundaryTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        install_safe_logging()

    def _capture(self, logger_name: str):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s context=%(context)s"))
        logger = logging.getLogger(logger_name)
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)
        self.addCleanup(logger.handlers.clear)
        return logger, stream

    def test_storage_and_provider_loggers_share_the_global_boundary(self):
        for logger_name in ("common.storage", "apps.providers.services"):
            with self.subTest(logger=logger_name):
                logger, stream = self._capture(logger_name)
                logger.info(
                    "operation completed",
                    extra={
                        "context": {
                            "storage_key": "tenant/evidence/private.jpg",
                            "client_secret": "provider-secret",
                            "external_reference": "customer-4482",
                            "device_fingerprint": "device-secret",
                            "user_agent": "browser-fingerprint",
                            "verification_subject_id": "vs_sensitive",
                            "provider_code": "safe-provider-code",
                        }
                    },
                )
                output = stream.getvalue()
                self.assertNotIn("tenant/evidence/private.jpg", output)
                self.assertNotIn("provider-secret", output)
                self.assertNotIn("customer-4482", output)
                self.assertNotIn("device-secret", output)
                self.assertNotIn("browser-fingerprint", output)
                self.assertNotIn("vs_sensitive", output)
                self.assertIn("safe-provider-code", output)

    def test_exception_objects_and_sensitive_mapping_keys_are_sanitized(self):
        logger, stream = self._capture("identitycore.argument-redaction-test")
        error = RuntimeError("token=exception-secret; email=subject@example.test")

        logger.error(
            "provider error: %s",
            error,
            extra={"context": {"subject@example.test": "lookup", "status": "failed"}},
        )

        output = stream.getvalue()
        self.assertNotIn("exception-secret", output)
        self.assertNotIn("subject@example.test", output)
        self.assertIn("RuntimeError", output)
        self.assertIn("failed", output)

    def test_interpolated_structures_and_bytes_are_redacted(self):
        logger, stream = self._capture("identitycore.structured-arguments-test")
        logger.info(
            "payload=%s binary=%s attempts=%03d",
            {"storage_key": "tenant/private.jpg", "status": "failed"},
            b"private-document-content",
            7,
            extra={"context": {}},
        )
        output = stream.getvalue()
        self.assertNotIn("tenant/private.jpg", output)
        self.assertNotIn("private-document-content", output)
        self.assertIn("failed", output)
        self.assertIn("attempts=007", output)

    def test_mapping_interpolation_preserves_exception_type_and_numbers(self):
        logger, stream = self._capture("identitycore.mapping-arguments-test")
        logger.error(
            "error=%(error)s; attempts=%(attempts)03d",
            {"error": RuntimeError("token=private-token"), "attempts": 7},
            extra={"context": {}},
        )
        output = stream.getvalue()
        self.assertNotIn("private-token", output)
        self.assertIn("RuntimeError", output)
        self.assertIn("attempts=007", output)

    def test_multiword_pii_in_free_text_is_fully_removed(self):
        logger, stream = self._capture("identitycore.multiword-redaction-test")
        logger.info(
            "review full_name=Ada Lovelace; external_reference=customer-4482; status=pending",
            extra={"context": {"status": "pending"}},
        )

        output = stream.getvalue()
        self.assertNotIn("Ada Lovelace", output)
        self.assertNotIn("customer-4482", output)
        self.assertIn("status=pending", output)

    def test_malformed_format_string_does_not_raise_or_render_arguments(self):
        logger, stream = self._capture("identitycore.format-error-test")
        logger.info(
            "provider failed without placeholder",
            "secret-that-must-not-render",
            extra={"context": {"status": "failed"}},
        )

        output = stream.getvalue()
        self.assertNotIn("secret-that-must-not-render", output)
        self.assertIn(LOG_FORMAT_ERROR, output)
        self.assertIn("failed", output)
