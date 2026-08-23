from __future__ import annotations

import logging
import re
import traceback
from collections.abc import Mapping
from threading import Lock
from typing import Any

REDACTED = "[REDACTED]"
REDACTED_BINARY = "[REDACTED_BINARY]"
MAX_REDACTION_DEPTH = 12

_SENSITIVE_KEYS = frozenset(
    {
        # Credentials and session material.
        "access_key",
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "cookie",
        "credentials",
        "csrf_token",
        "csrfmiddlewaretoken",
        "id_token",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "secret_access_key",
        "session_token",
        "set_cookie",
        "token",
        # Direct identifiers / PII.
        "address",
        "birth_date",
        "date_of_birth",
        "dob",
        "document_number",
        "email",
        "first_name",
        "full_name",
        "ghana_card_number",
        "last_name",
        "middle_name",
        "national_id",
        "passport_number",
        "phone",
        "phone_number",
        "postal_address",
        "tax_identification_number",
        "tin",
        # Evidence locations and raw document / biometric material.
        "biometric_payload",
        "biometric_template",
        "document_bytes",
        "document_image",
        "document_storage_key",
        "face_embedding",
        "face_image",
        "image",
        "image_base64",
        "image_bytes",
        "liveness_video",
        "mrz",
        "ocr_text",
        "raw_document",
        "raw_image",
        "raw_ocr",
        "selfie",
        "selfie_image",
        "selfie_storage_key",
        "storage_key",
    }
)

_SENSITIVE_SUFFIXES = (
    "_access_token",
    "_api_key",
    "_authorization",
    "_client_secret",
    "_credential",
    "_credentials",
    "_password",
    "_private_key",
    "_refresh_token",
    "_secret",
    "_session_token",
    "_storage_key",
    "_token",
)

_SENSITIVE_FRAGMENTS = (
    "biometric",
    "face_embedding",
    "image_base64",
    "image_bytes",
    "liveness_video",
    "selfie_image",
)

_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])",
    re.IGNORECASE,
)
_IPV4_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)")
_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(authorization|password|passcode|secret|token|api[_-]?key|client[_-]?secret|"
    r"access[_-]?key|refresh[_-]?token|session[_-]?token|cookie|email|phone(?:_number)?|"
    r"first[_-]?name|last[_-]?name|full[_-]?name|address|document[_-]?number|passport[_-]?number|"
    r"national[_-]?id|date[_-]?of[_-]?birth|dob|selfie(?:_image)?|image[_-]?base64|ocr[_-]?text|mrz|"
    r"biometric[_-]?(?:payload|template))\b"
    r"\s*[:=]\s*([\"']?)([^\s,;\"'}]+)\2"
)
_AWS_ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")

_INSTALL_LOCK = Lock()
_INSTALLED = False
_ORIGINAL_MAKE_RECORD = logging.Logger.makeRecord


def _normalize_key(key: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower())
    return normalized.strip("_")


def is_sensitive_key(key: object) -> bool:
    normalized = _normalize_key(key)
    if not normalized:
        return False
    if normalized in _SENSITIVE_KEYS:
        return True
    if normalized.endswith(_SENSITIVE_SUFFIXES):
        return True
    return any(fragment in normalized for fragment in _SENSITIVE_FRAGMENTS)


def redact_text(value: str) -> str:
    """Redact common secret and PII shapes from unstructured log text."""
    redacted = _BEARER_RE.sub("Bearer [REDACTED]", value)
    redacted = _JWT_RE.sub(REDACTED, redacted)
    redacted = _AWS_ACCESS_KEY_RE.sub(REDACTED, redacted)
    redacted = _CREDENTIAL_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group(1)}={REDACTED}", redacted
    )
    redacted = _EMAIL_RE.sub(REDACTED, redacted)
    redacted = _IPV4_RE.sub(REDACTED, redacted)
    redacted = _PHONE_RE.sub(REDACTED, redacted)
    return redacted


def redact_value(value: Any, *, key: object | None = None, _depth: int = 0) -> Any:
    """Return a logging-safe copy of a nested value.

    Redaction is key-aware for structured payloads and shape-aware for free text.
    Bytes are never logged because they can contain document or biometric evidence.
    """
    if key is not None and is_sensitive_key(key):
        return REDACTED
    if _depth >= MAX_REDACTION_DEPTH:
        return "[REDACTED_DEPTH_LIMIT]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return REDACTED_BINARY
    if isinstance(value, Mapping):
        return {
            str(item_key): redact_value(
                item_value,
                key=item_key,
                _depth=_depth + 1,
            )
            for item_key, item_value in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact_value(item, _depth=_depth + 1) for item in value)
    if isinstance(value, list):
        return [redact_value(item, _depth=_depth + 1) for item in value]
    if isinstance(value, (set, frozenset)):
        return [redact_value(item, _depth=_depth + 1) for item in value]
    return value


def _redact_exception(
    exc_info: tuple[type[BaseException], BaseException, Any],
) -> str:
    rendered = "".join(traceback.format_exception(*exc_info))
    return redact_text(rendered)


def sanitize_log_record(record: logging.LogRecord) -> logging.LogRecord:
    """Sanitize message args, structured extras, stack text, and exception text in place."""
    record.msg = redact_value(record.msg)
    if record.args:
        if isinstance(record.args, Mapping):
            record.args = redact_value(record.args)
        else:
            record.args = tuple(redact_value(item) for item in record.args)

    standard = set(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__)
    standard.update({"message", "asctime"})
    for field, value in list(record.__dict__.items()):
        if field in standard or field.startswith("_"):
            continue
        record.__dict__[field] = redact_value(value, key=field)

    if record.stack_info:
        record.stack_info = redact_text(record.stack_info)
    if record.exc_info:
        record.exc_text = _redact_exception(record.exc_info)
        record.exc_info = None
    elif record.exc_text:
        record.exc_text = redact_text(record.exc_text)
    return record


def _safe_make_record(self, *args, **kwargs):
    record = _ORIGINAL_MAKE_RECORD(self, *args, **kwargs)
    return sanitize_log_record(record)


def install_safe_logging() -> None:
    """Install the process-wide logging redaction boundary exactly once."""
    global _INSTALLED
    if _INSTALLED:
        return
    with _INSTALL_LOCK:
        if _INSTALLED:
            return
        logging.Logger.makeRecord = _safe_make_record
        _INSTALLED = True


__all__ = [
    "REDACTED",
    "REDACTED_BINARY",
    "install_safe_logging",
    "is_sensitive_key",
    "redact_text",
    "redact_value",
    "sanitize_log_record",
]
