import io
import logging

from django.test import SimpleTestCase

from common.safe_logging import install_safe_logging


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
