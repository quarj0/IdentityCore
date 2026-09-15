import io
import logging

from celery.utils.log import get_task_logger
from django.test import SimpleTestCase

from common.safe_logging import REDACTED, REDACTED_BINARY, install_safe_logging, redact_value


class SafeLoggingTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        install_safe_logging()

    def _capture(self, logger: logging.Logger, formatter: str = "%(levelname)s %(message)s"):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(formatter))
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)
        self.addCleanup(logger.handlers.clear)
        return stream

    def test_recursive_redaction_covers_secret_pii_and_biometric_fields(self):
        payload = {
            "authorization": "Bearer top-secret",
            "profile": {
                "email": "ada@example.test",
                "phone_number": "+233241234567",
                "document_number": "GHA-123456789",
                "safe_status": "pending_review",
            },
            "evidence": {
                "selfie_image": "base64-sensitive-selfie",
                "face_embedding": [0.1, 0.2, 0.3],
                "document_storage_key": "tenant/evidence/front.jpg",
            },
            "binary": b"document-bytes",
        }

        redacted = redact_value(payload)

        self.assertEqual(redacted["authorization"], REDACTED)
        self.assertEqual(redacted["profile"]["email"], REDACTED)
        self.assertEqual(redacted["profile"]["phone_number"], REDACTED)
        self.assertEqual(redacted["profile"]["document_number"], REDACTED)
        self.assertEqual(redacted["profile"]["safe_status"], "pending_review")
        self.assertEqual(redacted["evidence"]["selfie_image"], REDACTED)
        self.assertEqual(redacted["evidence"]["face_embedding"], REDACTED)
        self.assertEqual(redacted["evidence"]["document_storage_key"], REDACTED)
        self.assertEqual(redacted["binary"], REDACTED_BINARY)

    def test_django_logger_redacts_message_arguments_and_structured_extra(self):
        logger = logging.getLogger("django.identitycore.redaction-test")
        stream = self._capture(logger, "%(message)s payload=%(payload)s")

        logger.info(
            "request rejected email=%s Authorization: Bearer %s",
            "ada@example.test",
            "secret-access-token",
            extra={
                "payload": {
                    "password": "never-log-this",
                    "selfie_image": "raw-biometric-data",
                    "safe_reason": "credentials_missing",
                }
            },
        )

        output = stream.getvalue()
        self.assertNotIn("ada@example.test", output)
        self.assertNotIn("secret-access-token", output)
        self.assertNotIn("never-log-this", output)
        self.assertNotIn("raw-biometric-data", output)
        self.assertIn("credentials_missing", output)
        self.assertIn(REDACTED, output)

    def test_celery_task_logger_uses_the_same_redaction_boundary(self):
        logger = get_task_logger("identitycore.redaction-test")
        stream = self._capture(logger, "%(message)s context=%(context)s")

        logger.warning(
            "worker retry token=%s",
            "celery-secret-token",
            extra={
                "context": {
                    "api_key": "provider-key",
                    "ocr_text": "raw document text",
                    "verification_id": "ver_safe_public_id",
                }
            },
        )

        output = stream.getvalue()
        self.assertNotIn("celery-secret-token", output)
        self.assertNotIn("provider-key", output)
        self.assertNotIn("raw document text", output)
        self.assertIn("ver_safe_public_id", output)

    def test_exception_traceback_is_preserved_without_sensitive_values(self):
        logger = logging.getLogger("identitycore.exception-redaction-test")
        stream = self._capture(logger)

        try:
            raise RuntimeError(
                "token=runtime-secret email=ada@example.test "
                "phone=+233241234567 document_number=GHA-123456789"
            )
        except RuntimeError:
            logger.exception("provider failed first_name=Ada")

        output = stream.getvalue()
        self.assertIn("Traceback", output)
        self.assertIn("RuntimeError", output)
        self.assertNotIn("runtime-secret", output)
        self.assertNotIn("ada@example.test", output)
        self.assertNotIn("+233241234567", output)
        self.assertNotIn("GHA-123456789", output)
        self.assertNotIn("first_name=Ada", output)
        self.assertIn("first_name=[REDACTED]", output)
