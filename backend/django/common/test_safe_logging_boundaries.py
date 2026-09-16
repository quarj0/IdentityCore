import io
import logging
from decimal import Decimal

from django.test import SimpleTestCase
from django.test import RequestFactory, override_settings
from django.utils.log import AdminEmailHandler

from common.safe_logging import LOG_FORMAT_ERROR, install_safe_logging


class CapturingAdminEmailHandler(AdminEmailHandler):
    def __init__(self):
        super().__init__()
        self.sent_messages = []

    def send_mail(
        self, subject, message, *args, fail_silently=False, html_message=None, **kwargs
    ):
        self.sent_messages.append((subject, message, html_message))


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

    def test_admin_email_handler_receives_sanitized_exception_context(self):
        handler = CapturingAdminEmailHandler()
        logger = logging.getLogger("django.request.safe-email-test")
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.ERROR)
        self.addCleanup(logger.handlers.clear)

        try:
            raise RuntimeError("token=email-secret; status=failed")
        except RuntimeError:
            logger.exception("request failed")

        self.assertEqual(len(handler.sent_messages), 1)
        message = handler.sent_messages[0][1]
        self.assertIn(
            "test_admin_email_handler_receives_sanitized_exception_context", message
        )
        self.assertIn("RuntimeError", message)
        self.assertNotIn("email-secret", message)

    @override_settings(INTERNAL_IPS=["10.0.0.1"])
    def test_admin_email_handler_receives_safe_request_context(self):
        handler = CapturingAdminEmailHandler()
        logger = logging.getLogger("django.request.safe-request-email-test")
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.ERROR)
        self.addCleanup(logger.handlers.clear)
        request = RequestFactory().post(
            "/api/v1/verifications/",
            {"email": "subject@example.test", "token": "request-secret"},
            HTTP_AUTHORIZATION="Bearer auth-secret",
            REMOTE_ADDR="10.0.0.1",
        )
        request.user = "subject@example.test"

        try:
            raise RuntimeError("token=exception-secret")
        except RuntimeError:
            logger.exception("request failed", extra={"request": request})

        self.assertEqual(len(handler.sent_messages), 1)
        subject, message, html_message = handler.sent_messages[0]
        self.assertIn("internal IP", subject)
        self.assertIn("Request URL: http://testserver%5BREDACTED%5D", message)
        self.assertIn("POST", message)
        self.assertIn("REMOTE_ADDR = '[REDACTED]'", message)
        complete_report = message + (html_message or "")
        self.assertNotIn("subject@example.test", complete_report)
        self.assertNotIn("request-secret", complete_report)
        self.assertNotIn("auth-secret", complete_report)
        self.assertNotIn("exception-secret", complete_report)

    def test_admin_email_handler_redacts_identifiers_in_request_paths(self):
        handler = CapturingAdminEmailHandler()
        logger = logging.getLogger("django.request.safe-path-email-test")
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.ERROR)
        self.addCleanup(logger.handlers.clear)
        request = RequestFactory().get(
            "/api/v1/subjects/sub_sensitive_identifier?token=query-secret"
        )

        logger.error("request failed", extra={"request": request})

        subject, message, html_message = handler.sent_messages[0]
        complete_report = subject + message + (html_message or "")
        self.assertNotIn("sub_sensitive_identifier", complete_report)
        self.assertNotIn("query-secret", complete_report)
        self.assertIn("[REDACTED]", complete_report)

    def test_admin_email_handler_sanitizes_cached_and_lazy_query_data(self):
        for evaluate_get in (False, True):
            with self.subTest(evaluate_get=evaluate_get):
                handler = CapturingAdminEmailHandler()
                logger = logging.getLogger(f"django.request.safe-query-{evaluate_get}")
                logger.handlers = [handler]
                logger.propagate = False
                logger.setLevel(logging.ERROR)
                self.addCleanup(logger.handlers.clear)
                request = RequestFactory().get(
                    "/fail?access_token=verysecret&email=person@example.test"
                )
                if evaluate_get:
                    list(request.GET.items())

                logger.error("request failed", extra={"request": request})

                report = handler.sent_messages[0][1]
                self.assertIn("access_token = '[REDACTED]'", report)
                self.assertNotIn("verysecret", report)
                self.assertNotIn("person@example.test", report)

    def test_url_userinfo_is_redacted(self):
        from common.safe_logging import redact_text

        for value in (
            "redis://user:s3cr3t@redis:6379/0",
            "rediss://user:p%40ss@redis:6379/0",
            "https://token@provider.example/path",
        ):
            self.assertNotIn(value.split("@")[0].split("//", 1)[1], redact_text(value))
            self.assertIn("://[REDACTED]@", redact_text(value))
        self.assertEqual(
            redact_text("redis://redis:6379/0"),
            "redis://redis:6379/0",
        )

    def test_lazy_logging_values_cannot_abort_record_creation(self):
        class BrokenString:
            def __str__(self):
                raise RuntimeError("must not escape logging")

        logger, stream = self._capture("identitycore.lazy-string-test")
        logger.info("value=%s", BrokenString(), extra={"context": {}})
        logger.info(BrokenString(), extra={"context": {}})

        self.assertEqual(stream.getvalue().count(LOG_FORMAT_ERROR), 2)

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

    def test_decimal_values_preserve_numeric_log_formatting(self):
        logger, stream = self._capture("identitycore.decimal-format-test")
        logger.info(
            "score=%.2f",
            Decimal("0.976"),
            extra={"context": {}},
        )
        output = stream.getvalue()
        self.assertIn("score=0.98", output)
        self.assertNotIn(LOG_FORMAT_ERROR, output)

        extra_stream = io.StringIO()
        handler = logging.StreamHandler(extra_stream)
        handler.setFormatter(logging.Formatter("score=%(score).2f"))
        logger.handlers = [handler]
        logger.info("completed", extra={"score": Decimal("0.976")})
        self.assertIn("score=0.98", extra_stream.getvalue())

    def test_raw_ocr_result_shapes_are_redacted(self):
        from common.safe_logging import REDACTED, redact_value

        redacted = redact_value(
            {
                "raw_text_lines": ["ADA LOVELACE", "GHA-123456789"],
                "ocr": {
                    "lines": [
                        {"text": "ADA LOVELACE", "confidence": Decimal("0.98")}
                    ]
                },
                "summary": {"text": "safe operational summary"},
            }
        )
        self.assertEqual(redacted["raw_text_lines"], REDACTED)
        self.assertEqual(redacted["ocr"]["lines"][0]["text"], REDACTED)
        self.assertEqual(redacted["ocr"]["lines"][0]["confidence"], Decimal("0.98"))
        self.assertEqual(redacted["summary"]["text"], "safe operational summary")

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

    def test_all_sensitive_keys_are_redacted_in_serialized_text(self):
        from common.safe_logging import redact_text
        from shared.logging_redaction import _SENSITIVE_KEYS

        for key in _SENSITIVE_KEYS:
            for spelling in (key, key.replace("_", "-"), key.upper()):
                for message in (
                    f'{{"{spelling}":"private-value"}}',
                    f"?{spelling}=private-value&status=failed",
                    f"{spelling}='private-value'; status=failed",
                ):
                    with self.subTest(message=message):
                        self.assertNotIn("private-value", redact_text(message))
        for message in (
            '{"context":{"access_token":"private-value"}}',
            '{"face_embedding":["private-value", "second-private"]}',
            '{"private_key":"private-value\\"still-private"}',
            "full_name=Doe, Jane",
            'face_embedding=[\n  0.123,\n  0.456\n], "status":"failed"',
        ):
            self.assertNotIn("private-value", redact_text(message))
            self.assertNotIn("second-private", redact_text(message))
            self.assertNotIn("still-private", redact_text(message))
            self.assertNotIn("Jane", redact_text(message))
            self.assertNotIn("0.123", redact_text(message))
            self.assertNotIn("0.456", redact_text(message))

    def test_underscore_prefixed_extras_are_sanitized(self):
        logger, stream = self._capture("identitycore.private-extra-test")
        logger.handlers[0].setFormatter(logging.Formatter("%(_password)s %(_context)s"))
        logger.info(
            "request failed",
            extra={
                "_password": "private-password",
                "_context": {"token": "private-token"},
            },
        )
        self.assertNotIn("private-password", stream.getvalue())
        self.assertNotIn("private-token", stream.getvalue())

    def test_deployed_credentials_signatures_and_ipv6_are_redacted(self):
        from common.safe_logging import REDACTED, redact_text, redact_value

        for key in (
            "SECRET_KEY",
            "DJANGO_SECRET_KEY",
            "object_storage_access_key_id",
            "object_storage_secret_access_key",
            "aws_access_key_id",
            "aws_secret_access_key",
            "X-Amz-Signature",
            "X-IdentityCore-Signature",
            "SIGNING_KEY",
            "JWT_SIGNING_KEY",
            "previous_signing_key",
            "APPLICATION_ENCRYPTION_KEYRING",
            "handoff",
            "handoff_url",
            "recovery_codes",
            "mfa_recovery_codes",
        ):
            self.assertEqual(redact_value({key: "private-value"})[key], REDACTED)
            self.assertNotIn(
                "private-value", redact_text(f"?{key}=private-value&status=ok")
            )
        for address in (
            "2001:db8:1234:5678:9abc:def0:1234:5678",
            "2001:db8::1",
            "::1",
            "::ffff:192.0.2.1",
            "fe80::1%eth0",
        ):
            self.assertNotIn(address, redact_text(f"client connected from [{address}]"))
        self.assertEqual(
            redact_text("time 12:34:56; status=ok"), "time 12:34:56; status=ok"
        )
        self.assertNotIn(
            "private-value", redact_text("token=[REDACTED]private-value; status=ok")
        )

    def test_camel_case_sensitive_keys_are_redacted(self):
        from common.safe_logging import REDACTED, redact_value

        redacted = redact_value(
            {
                "accessToken": "access-private",
                "sessionToken": "session-private",
                "clientSecret": "client-private",
                "fullName": "Ada Private",
                "safeStatus": "ready",
            }
        )
        self.assertEqual(redacted["accessToken"], REDACTED)
        self.assertEqual(redacted["sessionToken"], REDACTED)
        self.assertEqual(redacted["clientSecret"], REDACTED)
        self.assertEqual(redacted["fullName"], REDACTED)
        self.assertEqual(redacted["safeStatus"], "ready")

    def test_missing_mapping_key_and_overflow_do_not_escape_logging(self):
        logger, stream = self._capture("identitycore.interpolation-failures-test")
        for message, argument in (
            ("%(missing)s", {"present": "private-value"}),
            ("%c", 0x110000),
        ):
            logger.info(message, argument, extra={"context": {}})
        self.assertEqual(stream.getvalue().count(LOG_FORMAT_ERROR), 2)
        self.assertNotIn("private-value", stream.getvalue())
