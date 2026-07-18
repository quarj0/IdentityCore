from __future__ import annotations

import hmac
import time
from hashlib import sha256
from typing import Union

from identitycore.errors import IdentityCoreError


def verify_webhook_signature(
    payload: Union[str, bytes],
    *,
    signature: str,
    timestamp: Union[str, int],
    signing_key: str,
    tolerance_seconds: int = 300,
    now: int | None = None,
) -> bool:
    """Verify an IdentityCore webhook using its unmodified request body."""
    if not signing_key:
        raise IdentityCoreError("signing_key is required.")
    if tolerance_seconds < 0:
        raise IdentityCoreError("tolerance_seconds cannot be negative.")
    try:
        sent_at = int(timestamp)
    except (TypeError, ValueError) as exc:
        raise IdentityCoreError("Webhook timestamp is invalid.") from exc
    current = int(time.time()) if now is None else int(now)
    if abs(current - sent_at) > tolerance_seconds:
        return False
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    digest = hmac.new(
        signing_key.encode("utf-8"),
        str(timestamp).encode("utf-8") + b"." + raw,
        sha256,
    ).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, str(signature))

