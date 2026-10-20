"""IdentityCore Provider SDK. Provider payloads and credentials must never be logged."""

from .contracts import OPERATION_CONTRACT, validate_binding, validate_result
from .runtime import ProviderRuntime, Response
from .store import SQLiteStore, WorkerLease, StorageUnavailable
from .wire import (
    ProtocolError,
    SigningKey,
    derive_signing_secret,
    json_bytes,
    parse_json,
    sign,
    verify,
)

__version__ = "0.1.0"
__all__ = [
    "OPERATION_CONTRACT",
    "ProviderRuntime",
    "Response",
    "SQLiteStore",
    "StorageUnavailable",
    "WorkerLease",
    "ProtocolError",
    "SigningKey",
    "derive_signing_secret",
    "json_bytes",
    "parse_json",
    "sign",
    "verify",
    "validate_binding",
    "validate_result",
]
