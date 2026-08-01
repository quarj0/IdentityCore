"""HMAC signing protocol for calls to external verification providers."""

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Callable, Mapping

from django.core.cache import cache

SIGNATURE_VERSION = "ic-provider-v1"


class ProviderSignatureError(ValueError):
    """Raised when a provider message cannot be authenticated."""


@dataclass(frozen=True)
class SignedMessage:
    key_id: str
    timestamp: int
    nonce: str
    signature: str

    def headers(self) -> dict[str, str]:
        return {
            "X-IC-Key-Id": self.key_id,
            "X-IC-Timestamp": str(self.timestamp),
            "X-IC-Nonce": self.nonce,
            "X-IC-Signature": self.signature,
            "X-IC-Signature-Version": SIGNATURE_VERSION,
        }


def canonical_json(value: object) -> bytes:
    """Serialize JSON identically across runtimes (UTF-8, sorted, no whitespace)."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_message(
    *, method: str, path: str, timestamp: int, nonce: str, body: bytes
) -> bytes:
    body_digest = hashlib.sha256(body).hexdigest()
    return "\n".join(
        (SIGNATURE_VERSION, method.upper(), path, str(timestamp), nonce, body_digest)
    ).encode("utf-8")


def sign_message(
    *,
    method: str,
    path: str,
    body: bytes,
    key_id: str,
    secret: str,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> SignedMessage:
    timestamp = int(time.time()) if timestamp is None else timestamp
    nonce = secrets.token_urlsafe(24) if nonce is None else nonce
    message = canonical_message(
        method=method, path=path, timestamp=timestamp, nonce=nonce, body=body
    )
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return SignedMessage(key_id, timestamp, nonce, signature)


def verify_message(
    *,
    method: str,
    path: str,
    body: bytes,
    headers: Mapping[str, str],
    keys: Mapping[str, str],
    max_age_seconds: int = 300,
    now: int | None = None,
    expected_nonce: str | None = None,
    replay_namespace: str = "provider-response",
    claim_nonce: Callable[[str, int], bool] | None = None,
) -> SignedMessage:
    """Verify freshness, key rotation, request binding, signature, and one-time use."""
    normalized = {key.lower(): value for key, value in headers.items()}
    try:
        key_id = normalized["x-ic-key-id"]
        timestamp = int(normalized["x-ic-timestamp"])
        nonce = normalized["x-ic-nonce"]
        signature = normalized["x-ic-signature"]
        version = normalized["x-ic-signature-version"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderSignatureError(
            "Missing or malformed provider signature headers."
        ) from exc
    if version != SIGNATURE_VERSION:
        raise ProviderSignatureError("Unsupported provider signature version.")
    secret = keys.get(key_id)
    if not secret:
        raise ProviderSignatureError("Unknown provider signing key.")
    current_time = int(time.time()) if now is None else now
    if abs(current_time - timestamp) > max_age_seconds:
        raise ProviderSignatureError("Provider message timestamp is stale.")
    if expected_nonce is not None and not hmac.compare_digest(nonce, expected_nonce):
        raise ProviderSignatureError(
            "Provider response is not bound to the request nonce."
        )
    expected = sign_message(
        method=method,
        path=path,
        body=body,
        key_id=key_id,
        secret=secret,
        timestamp=timestamp,
        nonce=nonce,
    ).signature
    if not hmac.compare_digest(signature, expected):
        raise ProviderSignatureError("Provider signature is invalid.")
    replay_key = hashlib.sha256(
        f"{replay_namespace}:{key_id}:{nonce}".encode()
    ).hexdigest()
    claim = claim_nonce or (lambda key, ttl: cache.add(key, True, timeout=ttl))
    if not claim(replay_key, max_age_seconds * 2):
        raise ProviderSignatureError("Provider message nonce has already been used.")
    return SignedMessage(key_id, timestamp, nonce, signature)
