"""Exact-wire HMAC authentication, freshness and mandatory atomic replay claims."""

from dataclasses import dataclass, field
from hashlib import sha256
import hmac
import json
import math
import re
import secrets
import time
from typing import Callable, Mapping

VERSION = "ic-provider-v1"
MAX_BODY_BYTES = 256 * 1024


class ProtocolError(ValueError):
    """A stable, value-free public error; never include received data in messages."""


@dataclass(frozen=True)
class SigningKey:
    key_id: str
    secret: str = field(repr=False)
    tenant_id: str
    environment: str
    capabilities: frozenset[str]


def derive_signing_secret(api_key: str) -> str:
    return hmac.new(
        api_key.encode("ascii"), b"identitycore-provider-hmac-v1", sha256
    ).hexdigest()


def json_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def parse_json(body: bytes):
    if len(body) > MAX_BODY_BYTES:
        raise ProtocolError("Provider message exceeds its size limit.")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ProtocolError("Duplicate JSON fields are forbidden.")
            result[key] = value
        return result

    def invalid(_):
        raise ProtocolError("Nonfinite JSON is forbidden.")

    try:
        value = json.loads(body, object_pairs_hook=pairs, parse_constant=invalid)
        if not isinstance(value, dict):
            raise ProtocolError("Provider messages must be objects.")

        def bounded(item, depth=0):
            if depth > 64 or isinstance(item, float) and not math.isfinite(item):
                raise ProtocolError("Provider JSON exceeds its structural limits.")
            if isinstance(item, dict):
                for child in item.values():
                    bounded(child, depth + 1)
            elif isinstance(item, list):
                for child in item:
                    bounded(child, depth + 1)

        bounded(value)
        return value
    except (UnicodeError, RecursionError, ValueError):
        raise ProtocolError("Provider JSON is invalid.") from None


def message(method: str, path: str, timestamp: int, nonce: str, body: bytes):
    return "\n".join(
        (VERSION, method.upper(), path, str(timestamp), nonce, sha256(body).hexdigest())
    ).encode("utf-8")


def sign(
    *, method: str, path: str, body: bytes, key: SigningKey, timestamp=None, nonce=None
):
    timestamp = int(time.time()) if timestamp is None else timestamp
    nonce = secrets.token_urlsafe(24) if nonce is None else nonce
    signature = hmac.new(
        key.secret.encode(), message(method, path, timestamp, nonce, body), sha256
    ).hexdigest()
    return {
        "X-IC-Key-Id": key.key_id,
        "X-IC-Timestamp": str(timestamp),
        "X-IC-Nonce": nonce,
        "X-IC-Signature-Version": VERSION,
        "X-IC-Signature": signature,
    }


def verify(
    *,
    method: str,
    path: str,
    body: bytes,
    headers: Mapping[str, str],
    keys: Mapping[str, SigningKey],
    claim_nonce: Callable[[str, int], bool],
    now=None,
    max_age_seconds=300,
    expected_nonce=None,
    replay_namespace="provider-request",
):
    if (
        len(body) > MAX_BODY_BYTES
        or not callable(claim_nonce)
        or type(max_age_seconds) is not int
        or max_age_seconds < 0
    ):
        raise ProtocolError("Provider authentication is unavailable.")
    normalized = {name.lower(): value for name, value in headers.items()}
    if len(normalized) != len(headers):
        raise ProtocolError("Provider authentication failed.")
    patterns = {
        "x-ic-key-id": r"[A-Za-z0-9_.-]{1,128}",
        "x-ic-timestamp": r"[0-9]{1,12}",
        "x-ic-nonce": r"[A-Za-z0-9_-]{1,256}",
        "x-ic-signature": r"[0-9a-f]{64}",
    }
    if any(
        not isinstance(normalized.get(name), str)
        or re.fullmatch(pattern, normalized[name]) is None
        for name, pattern in patterns.items()
    ):
        raise ProtocolError("Provider authentication failed.")
    if normalized.get("x-ic-signature-version") != VERSION:
        raise ProtocolError("Provider signature version is unsupported.")
    key = keys.get(normalized["x-ic-key-id"])
    current = int(time.time()) if now is None else now
    timestamp = int(normalized["x-ic-timestamp"])
    nonce = normalized["x-ic-nonce"]
    if (
        key is None
        or abs(current - timestamp) > max_age_seconds
        or (expected_nonce is not None and nonce != expected_nonce)
    ):
        raise ProtocolError("Provider authentication failed.")
    expected = sign(
        method=method, path=path, body=body, key=key, timestamp=timestamp, nonce=nonce
    )["X-IC-Signature"]
    if not hmac.compare_digest(normalized["x-ic-signature"], expected):
        raise ProtocolError("Provider authentication failed.")
    # Stable provider/direction scope excludes rotating configuration key IDs.
    # Every process accepting this provider identity must share the replay store.
    replay_key = sha256(
        json_bytes([VERSION, replay_namespace, key.tenant_id, key.environment, nonce])
    ).hexdigest()
    if claim_nonce(replay_key, timestamp + max_age_seconds + 1) is not True:
        raise ProtocolError("Provider nonce was already used.")
    return key, nonce
