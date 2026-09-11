import io
import logging

from app.core.safe_logging import REDACTED, install_safe_logging, redact_value


def _capture(logger: logging.Logger, formatter: str = "%(message)s"):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(formatter))
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return stream


def test_managed_ai_uses_shared_nested_redaction_corpus():
    install_safe_logging()
    payload = {
        "authorization": "Bearer ai-secret",
        "request": {
            "email": "subject@example.test",
            "document_number": "P1234567",
            "safe_operation": "face_compare",
        },
        "biometrics": {
            "face_embedding": [0.12, 0.34],
            "selfie_image": "base64-selfie",
        },
    }

    redacted = redact_value(payload)

    assert redacted["authorization"] == REDACTED
    assert redacted["request"]["email"] == REDACTED
    assert redacted["request"]["document_number"] == REDACTED
    assert redacted["request"]["safe_operation"] == "face_compare"
    # A container explicitly named "biometrics" is sensitive as a whole. The
    # redactor intentionally fails closed instead of retaining its structure.
    assert redacted["biometrics"] == REDACTED


def test_managed_ai_logger_redacts_structured_context_and_exception_text():
    install_safe_logging()
    logger = logging.getLogger("identitycore.ai.redaction-test")
    stream = _capture(logger, "%(message)s context=%(context)s")

    try:
        raise ValueError(
            "api_key=provider-secret email=subject@example.test "
            "image_base64=raw-biometric"
        )
    except ValueError:
        logger.exception(
            "AI processing failed Authorization: Bearer %s",
            "internal-shared-token",
            extra={
                "context": {
                    "document_storage_key": "tenant/evidence/document.jpg",
                    "ocr_text": "raw OCR contents",
                    "operation": "document_ocr",
                }
            },
        )

    output = stream.getvalue()
    assert "provider-secret" not in output
    assert "subject@example.test" not in output
    assert "raw-biometric" not in output
    assert "internal-shared-token" not in output
    assert "tenant/evidence/document.jpg" not in output
    assert "raw OCR contents" not in output
    assert "document_ocr" in output
    assert "Traceback" in output


def test_uvicorn_access_formatter_preserves_protocol_without_private_data():
    from uvicorn.logging import AccessFormatter

    install_safe_logging()
    logger = logging.getLogger("uvicorn.access")
    previous = (logger.handlers[:], logger.propagate, logger.level)
    stream = _capture(logger)
    logger.handlers[0].setFormatter(
        AccessFormatter(
            '%(client_addr)s - "%(request_line)s" %(status_code)s', use_colors=False
        )
    )
    try:
        logger.info(
            '%s - "%s %s HTTP/%s" %d',
            "192.0.2.1:1234",
            "GET",
            "/check?access_token=private-token",
            "1.1",
            200,
        )
        output = stream.getvalue()
        assert "GET" in output
        assert "200 OK" in output
        assert "private-token" not in output
        assert "192.0.2.1" not in output
        assert "HTTP/1.1" in output
    finally:
        logger.handlers, logger.propagate, logger.level = previous
