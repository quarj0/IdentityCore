from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings


FIELD_ENVELOPE_VERSION = "ic-field-v1"
OBJECT_ENVELOPE_VERSION = "ic-object-v1"


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


@dataclass(frozen=True)
class KeyMaterial:
    key_id: str
    key_bytes: bytes


def _parse_keyring(value: str) -> list[KeyMaterial]:
    keyring: list[KeyMaterial] = []
    for item in [part.strip() for part in value.split(",") if part.strip()]:
        key_id, _, encoded_key = item.partition(":")
        if not key_id or not encoded_key:
            raise ValueError("APPLICATION_ENCRYPTION_KEYRING entries must use key_id:base64urlkey format.")
        key_bytes = _b64decode(encoded_key.strip())
        if len(key_bytes) != 32:
            raise ValueError("Application encryption keys must decode to 32 bytes.")
        keyring.append(KeyMaterial(key_id=key_id.strip(), key_bytes=key_bytes))
    return keyring


def _derive_default_key() -> KeyMaterial:
    secret = settings.SECRET_KEY.encode("utf-8")
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"identitycore-application-encryption",
        info=b"identitycore/default-keyring",
    ).derive(secret)
    return KeyMaterial(key_id="derived-v1", key_bytes=derived)


def get_application_keyring() -> list[KeyMaterial]:
    configured = getattr(settings, "APPLICATION_ENCRYPTION_KEYRING", "").strip()
    if configured:
        return _parse_keyring(configured)
    return [_derive_default_key()]


def get_active_key() -> KeyMaterial:
    keyring = get_application_keyring()
    active_key_id = getattr(settings, "APPLICATION_ENCRYPTION_ACTIVE_KEY_ID", "").strip()
    if active_key_id:
        for key in keyring:
            if key.key_id == active_key_id:
                return key
        raise ValueError(
            f"Active application encryption key '{active_key_id}' is not present in the configured keyring."
        )
    return keyring[0]


def get_key_by_id(key_id: str) -> KeyMaterial:
    for key in get_application_keyring():
        if key.key_id == key_id:
            return key
    raise ValueError(f"Unknown application encryption key id '{key_id}'.")


def _build_field_aad(purpose: str) -> bytes:
    return f"identitycore:field:{purpose}".encode("utf-8")


def _build_object_aad(purpose: str) -> bytes:
    return f"identitycore:object:{purpose}".encode("utf-8")


def encrypt_json_value(value, *, purpose: str) -> dict:
    plaintext = json.dumps(
        value,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    active_key = get_active_key()
    nonce = os.urandom(12)
    ciphertext = AESGCM(active_key.key_bytes).encrypt(
        nonce,
        plaintext,
        _build_field_aad(purpose),
    )
    return {
        "__enc__": FIELD_ENVELOPE_VERSION,
        "alg": "AES-256-GCM",
        "kid": active_key.key_id,
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
    }


def decrypt_json_value(value, *, purpose: str):
    if not isinstance(value, dict) or value.get("__enc__") != FIELD_ENVELOPE_VERSION:
        return value
    key = get_key_by_id(value["kid"])
    plaintext = AESGCM(key.key_bytes).decrypt(
        _b64decode(value["nonce"]),
        _b64decode(value["ciphertext"]),
        _build_field_aad(purpose),
    )
    return json.loads(plaintext.decode("utf-8"))


def encrypt_object_bytes(
    *,
    content: bytes,
    content_type: str,
    purpose: str,
) -> bytes:
    active_key = get_active_key()
    nonce = os.urandom(12)
    ciphertext = AESGCM(active_key.key_bytes).encrypt(
        nonce,
        content,
        _build_object_aad(purpose),
    )
    envelope = {
        "__enc__": OBJECT_ENVELOPE_VERSION,
        "alg": "AES-256-GCM",
        "kid": active_key.key_id,
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
        "content_type": content_type,
    }
    return json.dumps(envelope, separators=(",", ":")).encode("utf-8")


def decrypt_object_bytes(
    *,
    payload: bytes,
    purpose: str,
) -> tuple[bytes, str]:
    envelope = json.loads(payload.decode("utf-8"))
    if envelope.get("__enc__") != OBJECT_ENVELOPE_VERSION:
        raise ValueError("Object payload is not an IdentityCore encrypted object.")
    key = get_key_by_id(envelope["kid"])
    content = AESGCM(key.key_bytes).decrypt(
        _b64decode(envelope["nonce"]),
        _b64decode(envelope["ciphertext"]),
        _build_object_aad(purpose),
    )
    return content, envelope["content_type"]


def is_encrypted_object_payload(payload: bytes) -> bool:
    try:
        envelope = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return envelope.get("__enc__") == OBJECT_ENVELOPE_VERSION
