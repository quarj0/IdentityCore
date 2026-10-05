"""Versioned tenant DEKs with authenticated wrapping and ownership binding."""

import json
import os
import re
from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
from hashlib import sha256
from time import monotonic

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.db import IntegrityError, transaction

from common.crypto import _b64decode, _b64encode, decrypt_json_value, encrypt_json_value

TENANT_FIELD_VERSION = "ic-tenant-field-v2"
TENANT_OBJECT_VERSION = "ic-tenant-object-v2"
read_key_records = ContextVar("tenant_decryption_key_records", default=None)
operation_deks = ContextVar("tenant_operation_deks", default=None)


@contextmanager
def key_operation():
    # One request or bounded rotation batch; never shared across operations.
    values = {}
    token = operation_deks.set(values)
    try:
        yield
    finally:
        values.clear()
        operation_deks.reset(token)


def bounded_key_operation(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with key_operation():
            return function(*args, **kwargs)

    return wrapped


SCOPE = re.compile(r"^ten_[0-9A-HJKMNP-TV-Z]{26}$")


def validate_scope(scope):
    if not isinstance(scope, str) or not SCOPE.fullmatch(scope):
        raise ValueError("A valid tenant encryption scope is required.")
    return scope


def validate_environment(environment):
    if environment not in {"sandbox", "production", "shared"}:
        raise ValueError("A valid encryption environment is required.")
    return environment


def wrapping_purpose(scope, version, environment):
    return f"tenant.data-key:{scope}:{validate_environment(environment)}:{version}"


def wrap_key(scope, version, key, environment):
    if environment != "shared":
        from apps.tenants.models import TenantKMSBinding
        from common.customer_kms import wrap

        binding = (
            TenantKMSBinding.objects.filter(
                tenant__public_id=scope,
                environment=environment,
                active=True,
                deleted_at__isnull=True,
            )
            .select_related("tenant")
            .first()
        )
        if binding is not None:
            result = wrap(binding, key, version)
            result["__wrapper"] = "aws_kms"
            return result
    return encrypt_json_value(
        {"key": _b64encode(key)}, purpose=wrapping_purpose(scope, version, environment)
    )


def unwrap_key(record, expected_scope, environment):
    if (
        record.tenant_scope != validate_scope(expected_scope)
        or record.environment != validate_environment(environment)
    ) or record.deleted_at is not None:
        raise ValueError("Tenant encryption key is unavailable.")
    if record.wrapping_provider == "aws_kms":
        from apps.tenants.models import TenantKMSBinding
        from common.customer_kms import assert_binding, unwrap

        try:
            binding = TenantKMSBinding.objects.select_related("tenant").get(
                public_id=record.wrapped_key_json["binding_id"]
            )
            assert_binding(binding, expected_scope, environment)
            cache = operation_deks.get()
            cache_id = (
                expected_scope,
                environment,
                record.public_id,
                record.version,
                binding.public_id,
                sha256(
                    json.dumps(record.wrapped_key_json, sort_keys=True).encode()
                ).digest(),
            )
            entry = cache.get(cache_id) if cache is not None else None
            # Fresh binding checks above apply on cache hits too. Short TTL bounds
            # remote revocation staleness inside an operation; the next operation
            # always contacts KMS again.
            now = monotonic()
            if entry is not None and now - entry[0] < 5:
                return entry[1]
            key = unwrap(binding, record.wrapped_key_json, record.version)
            if cache is not None:
                if len(cache) >= 16:
                    cache.clear()
                cache[cache_id] = (monotonic(), key)
            return key
        except Exception:
            raise ValueError("Tenant encryption key is unavailable.") from None
    if record.wrapping_provider != "platform":
        raise ValueError("Tenant key wrapping provider is unavailable.")
    if (
        not isinstance(record.wrapped_key_json, dict)
        or record.wrapped_key_json.get("__enc__") != "ic-field-v1"
    ):
        raise ValueError("Tenant encryption key is unavailable.")
    try:
        wrapped = decrypt_json_value(
            record.wrapped_key_json,
            purpose=wrapping_purpose(expected_scope, record.version, environment),
        )
        key = _b64decode(wrapped["key"])
        if len(key) != 32:
            raise ValueError
        return key
    except Exception:
        raise ValueError("Tenant encryption key is unavailable.") from None


def active_key(scope, environment="shared"):
    from apps.tenants.models import TenantDataKey

    scope = validate_scope(scope)
    environment = validate_environment(environment)
    record = TenantDataKey.objects.filter(
        tenant_scope=scope,
        environment=environment,
        active=True,
        deleted_at__isnull=True,
    ).first()
    if record:
        return record
    if TenantDataKey.objects.filter(
        tenant_scope=scope, environment=environment
    ).exists():
        # A concurrent first writer may commit between the initial read and
        # this existence check. Re-read before interpreting retained keys as
        # a deliberately disabled scope.
        record = TenantDataKey.objects.filter(
            tenant_scope=scope,
            environment=environment,
            active=True,
            deleted_at__isnull=True,
        ).first()
        if record is not None:
            return record
        raise ValueError("No active tenant encryption key is available.")
    wrapped = wrap_key(scope, 1, os.urandom(32), environment)
    try:
        with transaction.atomic():
            record, _ = TenantDataKey.objects.get_or_create(
                tenant_scope=scope,
                environment=environment,
                version=1,
                defaults={
                    "active": True,
                    "wrapped_key_json": wrapped,
                    "wrapping_provider": wrapped.get("__wrapper", "platform"),
                },
            )
    except IntegrityError:
        record = TenantDataKey.objects.get(
            tenant_scope=scope,
            environment=environment,
            active=True,
            deleted_at__isnull=True,
        )
    if not record.active or record.deleted_at is not None:
        raise ValueError("No active tenant encryption key is available.")
    return record


def aad(scope, version, purpose, kind, environment, content_type=""):
    if not isinstance(purpose, str) or not purpose:
        raise ValueError("An encryption purpose is required.")
    return json.dumps(
        [
            "identitycore",
            kind,
            validate_scope(scope),
            validate_environment(environment),
            version,
            purpose,
            content_type,
        ],
        separators=(",", ":"),
    ).encode()


def encrypt_tenant_bytes(
    content, *, tenant_scope, purpose, kind, environment="shared", content_type=""
):
    record = active_key(tenant_scope, environment)
    key = unwrap_key(record, tenant_scope, environment)
    nonce = os.urandom(12)
    encrypted = AESGCM(key).encrypt(
        nonce,
        content,
        aad(tenant_scope, record.version, purpose, kind, environment, content_type),
    )
    envelope = {
        "__enc__": kind,
        "alg": "AES-256-GCM",
        "tenant": tenant_scope,
        "environment": environment,
        "kid": record.public_id,
        "version": record.version,
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(encrypted),
    }
    if content_type:
        envelope["content_type"] = content_type
    return envelope


def decrypt_tenant_bytes(
    envelope, *, tenant_scope, purpose, kind, environment="shared"
):
    from apps.tenants.models import TenantDataKey

    validate_scope(tenant_scope)
    validate_environment(environment)
    if (
        not isinstance(envelope, dict)
        or envelope.get("__enc__") != kind
        or envelope.get("tenant") != tenant_scope
        or envelope.get("environment") != environment
        or envelope.get("alg") != "AES-256-GCM"
        or type(envelope.get("version")) is not int
    ):
        raise ValueError("Tenant encrypted content is unavailable.")
    try:
        cache = read_key_records.get()
        cache_id = (envelope["kid"], tenant_scope, environment, envelope["version"])
        record = cache.get(cache_id) if cache is not None else None
        if record is None:
            record = TenantDataKey.objects.get(
                public_id=envelope["kid"],
                tenant_scope=tenant_scope,
                environment=environment,
                version=envelope["version"],
                deleted_at__isnull=True,
            )
            if cache is not None:
                cache[cache_id] = record
        key = unwrap_key(record, tenant_scope, environment)
        return AESGCM(key).decrypt(
            _b64decode(envelope["nonce"]),
            _b64decode(envelope["ciphertext"]),
            aad(
                tenant_scope,
                record.version,
                purpose,
                kind,
                environment,
                envelope.get("content_type", ""),
            ),
        )
    except Exception:
        raise ValueError("Tenant encrypted content is unavailable.") from None


def encrypt_tenant_json(value, *, tenant_scope, purpose, environment="shared"):
    return encrypt_tenant_bytes(
        json.dumps(value, separators=(",", ":"), sort_keys=True, default=str).encode(),
        tenant_scope=tenant_scope,
        purpose=purpose,
        kind=TENANT_FIELD_VERSION,
        environment=environment,
    )


def decrypt_tenant_json(value, *, tenant_scope, purpose, environment="shared"):
    if not isinstance(value, dict) or value.get("__enc__") != TENANT_FIELD_VERSION:
        return decrypt_json_value(value, purpose=purpose)
    return json.loads(
        decrypt_tenant_bytes(
            value,
            tenant_scope=tenant_scope,
            purpose=purpose,
            kind=TENANT_FIELD_VERSION,
            environment=environment,
        ).decode()
    )
