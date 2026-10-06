"""Versioned audit payloads; retain these formats for historical verification."""

import hashlib
import hmac
import json

from common.crypto import get_key_by_id


def event_payload(event):
    payload = {
        name: getattr(event, name)
        for name in (
            "tenant_id",
            "actor_type",
            "actor_id",
            "action",
            "target_type",
            "target_id",
            "ip_address",
            "user_agent",
            "device_fingerprint",
            "metadata_json",
            "sensitive_metadata_hash",
            "previous_event_hash",
        )
    }
    payload["created_at"] = event.created_at.isoformat()
    if event.integrity_version == 2:
        payload["public_id"] = event.public_id
    elif event.integrity_version != 1:
        raise ValueError("Unsupported audit integrity version.")
    return payload


def encoded_payload(event):
    return json.dumps(
        event_payload(event), sort_keys=True, default=str, separators=(",", ":")
    ).encode("utf-8")


def event_hash(event):
    return hashlib.sha256(encoded_payload(event)).hexdigest()


def event_authentication(event):
    key = get_key_by_id(event.integrity_key_id)
    # Derive a separate audit key from the retained application keyring.
    audit_key = hmac.digest(key.key_bytes, b"identitycore:audit:key:v1", "sha256")
    envelope = json.dumps(
        {
            "version": event.integrity_version,
            "key_id": event.integrity_key_id,
            "public_id": event.public_id,
            "integrity_hash": event.integrity_hash,
            "payload": event_payload(event),
        },
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(
        audit_key, b"identitycore:audit:event:v1\0" + envelope, hashlib.sha256
    ).hexdigest()
