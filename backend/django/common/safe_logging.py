from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from shared.logging_redaction import (  # noqa: E402
    LOG_FORMAT_ERROR,
    REDACTED,
    REDACTED_BINARY,
    install_safe_logging,
    is_sensitive_key,
    redact_text,
    redact_value,
    sanitize_log_record,
)

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
