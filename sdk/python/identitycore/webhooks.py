from __future__ import annotations

import hmac
import json
import time
from hashlib import sha256
from collections.abc import MutableSet, Sequence
from typing import Union

from identitycore.errors import IdentityCoreError


def verify_webhook_signature(
    payload: Union[str, bytes],
    *,
    signature: str,
    timestamp: Union[str, int],
    event_id: str | None = None,
    signing_key: str | None = None,
    signing_keys: Sequence[str] | None = None,
    tolerance_seconds: int = 300,
    now: int | None = None,
    seen_event_ids: MutableSet[str] | None = None,
) -> bool:
    """Verify a v1 webhook and optionally reject already-seen event IDs."""
    candidate_secrets = [key for key in (signing_keys or []) if key]
    if signing_key:
        candidate_secrets.insert(0, signing_key)
    if not candidate_secrets:
        raise IdentityCoreError("At least one signing secret is required.")
    if not event_id:
        raise IdentityCoreError("event_id is required for v1 signatures.")
    if tolerance_seconds < 0:
        raise IdentityCoreError("tolerance_seconds cannot be negative.")
    try:
        sent_at = int(timestamp)
        current = int(time.time()) if now is None else int(now)
    except (TypeError, ValueError) as exc:
        raise IdentityCoreError("Webhook timestamp is invalid.") from exc
    if abs(current - sent_at) > tolerance_seconds:
        return False
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    message = (
        str(timestamp).encode("utf-8") + b"." + event_id.encode("utf-8") + b"." + raw
    )
    valid = any(
        hmac.compare_digest(
            f"v1={hmac.new(sha256(secret.encode()).hexdigest().encode(), message, sha256).hexdigest()}",
            str(signature),
        )
        for secret in candidate_secrets
    )
    if not valid:
        return False
    try:
        document = json.loads(raw)
    except (TypeError, ValueError, UnicodeDecodeError):
        return False
    if not isinstance(document, dict):
        return False
    if document.get("id") != event_id or document.get("schema_version") != "1":
        return False
    if seen_event_ids is not None:
        if event_id in seen_event_ids:
            return False
        seen_event_ids.add(event_id)
    return True
