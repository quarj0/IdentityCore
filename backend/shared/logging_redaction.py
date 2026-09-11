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
LOG_FORMAT_ERROR = "[LOG_FORMAT_ERROR]"

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
        # Direct identifiers / PII / correlation values that may identify a subject.
        "address",
        "birth_date",
        "client_ip",
        "date_of_birth",
        "device_fingerprint",
        "dob",
        "document_number",
        "email",
        "external_reference",
        "first_name",
        "full_name",
        "ghana_card_number",
        "ip",
        "ip_address",
        "last_name",
        "middle_name",
        "national_id",
        "passport_number",
        "phone",
        "phone_number",
        "postal_address",
        "remote_addr",
        "subject_id",
        "tax_identification_number",
        "tin",
        "user_agent",
        "verification_subject_id",
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
    "_fingerprint",
    "_password",
    "_private_key",
    "_refresh_token",
    "_secret",
    "_session_token",
    "_storage_key",
    "_subject_id",
    "_token",
    "_user_agent",
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
    r"national[_-]?id|date[_-]?of[_-]?birth|dob|external[_-]?reference|device[_-]?fingerprint|"
    r"subject[_-]?id|verification[_-]?subject[_-]?id|client[_-]?ip|ip[_-]?address|remote[_-]?addr|"
    r"user[_-]?agent|selfie(?:_image)?|image[_-]?base64|ocr[_-]?text|mrz|"
    r"biometric[_-]?(?:payload|template))\b"
    r"\s*[:=]\s*([\"']?)([^,;\n\r\"'}]+)\2"
)
_AWS_ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_STANDARD_LOG_RECORD_ATTRS = frozenset(
    {
        *logging.LogRecord(None, 0, "", 0, "", (), None).__dict__.keys(),
        "asctime",
        "message",
    }
)

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
    if isinstance(value, BaseException):
        return f"{value.__class__.__name__}: {redact_text(str(value))}"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return REDACTED_BINARY
    if isinstance(value, Mapping):
        redacted_mapping = {}
        for item_key, item_value in value.items():
            safe_key = redact_text(str(item_key))
            redacted_mapping[safe_key] = redact_value(
                item_value,
                key=item_key,
                _depth=_depth + 1,
            )
        return redacted_mapping
    if isinstance(value, tuple):
        return tuple(redact_value(item, _depth=_depth + 1) for item in value)
    if isinstance(value, list):
        return [redact_value(item, _depth=_depth + 1) for item in value]
    if isinstance(value, (set, frozenset)):
        return [redact_value(item, _depth=_depth + 1) for item in value]
    return redact_text(str(value))


def _redact_exception(
    exc_info: tuple[type[BaseException], BaseException, Any],
) -> str:
    rendered = "".join(traceback.format_exception(*exc_info))
    return redact_text(rendered)


def sanitize_log_record(record: logging.LogRecord) -> logging.LogRecord:
    """Sanitize rendered messages, structured extras, stack text, and exceptions."""
    if record.args:
        # Preserve structured redaction and exception types before interpolation
        # turns arguments into plain text. Numeric arguments retain their types.
        if isinstance(record.args, Mapping):
            record.args = {
                key: redact_value(value, key=key) for key, value in record.args.items()
            }
        else:
            record.args = redact_value(record.args)
        # Render once using Python logging's normal interpolation rules, then redact
        # the complete result. If the caller supplied a malformed format string,
        # discard the args instead of letting logging break request/worker execution.
        try:
            rendered_message = record.getMessage()
        except (TypeError, ValueError):
            rendered_message = f"{redact_value(record.msg)} {LOG_FORMAT_ERROR}"
        record.msg = redact_text(str(rendered_message))
        record.args = ()
    else:
        record.msg = redact_value(record.msg)

    for field, value in list(record.__dict__.items()):
        if field in _STANDARD_LOG_RECORD_ATTRS or field.startswith("_"):
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
    "LOG_FORMAT_ERROR",
    "REDACTED",
    "REDACTED_BINARY",
    "install_safe_logging",
    "is_sensitive_key",
    "redact_text",
    "redact_value",
    "sanitize_log_record",
]
