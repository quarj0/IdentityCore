"""Bounded, process-local proofs for repeated bearer credential verification.

Only successful password-hash checks are cached. Keys are keyed digests of
both the credential and its current database hash, never raw bearer tokens.
Callers must still check current database authorization, expiry and revocation.
"""

from collections import OrderedDict
import hashlib
import hmac
import secrets
from threading import Lock
import time

from django.contrib.auth.hashers import check_password

_KEY = secrets.token_bytes(32)
_PROOFS = OrderedDict()
_LOCK = Lock()
_CHECK_LOCKS = tuple(Lock() for _ in range(64))
_TTL_SECONDS = 300
_MAX_PROOFS = 2048


def verify_bearer_secret(raw_secret: str, encoded_hash: str) -> bool:
    if encoded_hash.startswith("bearer_sha256$"):
        expected = hashlib.sha256(raw_secret.encode()).hexdigest()
        return hmac.compare_digest(encoded_hash, "bearer_sha256$" + expected)
    if not raw_secret or not encoded_hash:
        return False
    proof = hmac.digest(
        _KEY, (encoded_hash + "\0" + raw_secret).encode(), hashlib.sha256
    )
    now = time.monotonic()
    with _LOCK:
        expires = _PROOFS.get(proof)
        if expires is not None and expires > now:
            _PROOFS.move_to_end(proof)
            return True
        _PROOFS.pop(proof, None)
    # Coalesce concurrent first use of the same proof within each process.
    # A fixed stripe array bounds memory even under invalid credential traffic.
    with _CHECK_LOCKS[proof[0] % len(_CHECK_LOCKS)]:
        with _LOCK:
            expires = _PROOFS.get(proof)
            if expires is not None and expires > time.monotonic():
                _PROOFS.move_to_end(proof)
                return True
        if not check_password(raw_secret, encoded_hash):
            return False
        with _LOCK:
            _PROOFS[proof] = time.monotonic() + _TTL_SECONDS
            _PROOFS.move_to_end(proof)
            while len(_PROOFS) > _MAX_PROOFS:
                _PROOFS.popitem(last=False)
        return True


def hash_generated_bearer(raw_secret: str) -> str:
    """Hash a server-generated 256-bit token; never use for user passwords."""
    if len(raw_secret) < 43:
        raise ValueError("Generated bearer credentials require 256-bit tokens")
    return "bearer_sha256$" + hashlib.sha256(raw_secret.encode()).hexdigest()
