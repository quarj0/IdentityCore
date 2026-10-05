"""Customer symmetric KMS wrapping; AWS CloudHSM-backed KMS keys use this API."""

import hmac
import os
import re

import boto3
from botocore.config import Config
from django.db import transaction
from django.utils import timezone

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.tenants.models import TenantKMSBinding
from common.crypto import _b64decode, _b64encode

ARN = re.compile(
    r"^arn:(aws|aws-cn|aws-us-gov):kms:([a-z0-9-]{5,30}):([0-9]{12}):key/([a-f0-9-]{36}|mrk-[a-f0-9]{32})$"
)
ERROR = "Customer key provider is unavailable."


def validate_arn(value):
    match = ARN.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ValueError("Use a symmetric KMS key ARN.")
    session = boto3.session.Session()
    if match[2] not in session.get_available_regions("kms", partition_name=match[1]):
        raise ValueError("The KMS key region is unsupported.")
    return match[2]


def client_for(binding):
    return boto3.client(
        "kms",
        region_name=validate_arn(binding.key_arn),
        config=Config(
            connect_timeout=2, read_timeout=2, retries={"total_max_attempts": 1}
        ),
    )


def context(binding, version):
    return {
        "binding": binding.public_id,
        "tenant": binding.tenant.public_id,
        "environment": binding.environment,
        "version": str(version),
        "purpose": "identitycore-tenant-dek-v1",
    }


def tokens(binding):
    values = binding.grant_tokens_json
    if (
        not isinstance(values, list)
        or len(values) > 10
        or any(
            not isinstance(value, str) or not 1 <= len(value) <= 4096
            for value in values
        )
    ):
        raise ValueError(ERROR)
    return {"GrantTokens": values} if values else {}


def assert_binding(binding, scope, environment, *, writing=False):
    if (
        binding.tenant.public_id != scope
        or binding.environment != environment
        or binding.deleted_at is not None
        or binding.status not in ({"active"} if writing else {"active", "retired"})
        or (writing and not binding.active)
    ):
        raise ValueError(ERROR)


def wrap(binding, key, version, *, probe=False):
    try:
        if not probe:
            assert_binding(
                binding, binding.tenant.public_id, binding.environment, writing=True
            )
        response = client_for(binding).encrypt(
            KeyId=binding.key_arn,
            Plaintext=key,
            EncryptionAlgorithm="SYMMETRIC_DEFAULT",
            EncryptionContext=context(binding, version),
            **tokens(binding)
        )
        if response.get("KeyId") != binding.key_arn or not isinstance(
            response.get("CiphertextBlob"), bytes
        ):
            raise ValueError(ERROR)
        return {
            "binding_id": binding.public_id,
            "key_arn": binding.key_arn,
            "ciphertext": _b64encode(response["CiphertextBlob"]),
        }
    except Exception:
        raise ValueError(ERROR) from None


def unwrap(binding, envelope, version, *, probe=False):
    try:
        if not probe:
            assert_binding(binding, binding.tenant.public_id, binding.environment)
        if (
            envelope.get("binding_id") != binding.public_id
            or envelope.get("key_arn") != binding.key_arn
        ):
            raise ValueError(ERROR)
        response = client_for(binding).decrypt(
            KeyId=binding.key_arn,
            CiphertextBlob=_b64decode(envelope["ciphertext"]),
            EncryptionAlgorithm="SYMMETRIC_DEFAULT",
            EncryptionContext=context(binding, version),
            **tokens(binding)
        )
        key = response.get("Plaintext")
        if (
            response.get("KeyId") != binding.key_arn
            or not isinstance(key, bytes)
            or len(key) != 32
        ):
            raise ValueError(ERROR)
        return key
    except Exception:
        raise ValueError(ERROR) from None


def validate_connection(binding):
    validate_arn(binding.key_arn)
    try:
        metadata = client_for(binding).describe_key(
            KeyId=binding.key_arn, **tokens(binding)
        )["KeyMetadata"]
        if (
            metadata.get("Arn") != binding.key_arn
            or metadata.get("KeyState") != "Enabled"
            or metadata.get("KeyUsage") != "ENCRYPT_DECRYPT"
            or metadata.get("KeySpec") != "SYMMETRIC_DEFAULT"
            or metadata.get("KeyManager") != "CUSTOMER"
        ):
            raise ValueError(ERROR)
        probe = os.urandom(32)
        encrypted = wrap(binding, probe, 0, probe=True)
        if not hmac.compare_digest(unwrap(binding, encrypted, 0, probe=True), probe):
            raise ValueError(ERROR)
    except Exception:
        raise ValueError(ERROR) from None


@transaction.atomic
def activate(binding, *, actor=None, request=None):
    lock_audit_chain(binding.tenant_id)
    binding = (
        TenantKMSBinding.objects.select_for_update(no_key=True)
        .select_related("tenant")
        .get(pk=binding.pk)
    )
    validate_connection(binding)
    TenantKMSBinding.objects.filter(
        tenant=binding.tenant, environment=binding.environment, active=True
    ).exclude(pk=binding.pk).update(active=False, status="retired")
    binding.active, binding.status, binding.validated_at = (
        True,
        "active",
        timezone.now(),
    )
    binding.save(update_fields=["active", "status", "validated_at", "updated_at"])
    from common.tenant_key_rotation import start_rotation

    job = start_rotation(binding.tenant.public_id, binding.environment, actor=actor)
    record_audit_event(
        tenant=binding.tenant,
        actor=actor,
        request=request,
        action="encryption.kms_activated",
        target_type="tenant_kms_binding",
        target_id=binding.public_id,
        metadata={
            "environment": binding.environment,
            "key_arn": binding.key_arn,
            "rotation_id": job.public_id,
        },
    )
    return binding, job


@transaction.atomic
def disable(binding, *, actor=None, request=None):
    lock_audit_chain(binding.tenant_id)
    binding = (
        TenantKMSBinding.objects.select_for_update(no_key=True)
        .select_related("tenant")
        .get(pk=binding.pk)
    )
    binding.status = "disabled"
    # Keep the active pointer: disablement must not silently choose platform wrapping.
    binding.save(update_fields=["status", "updated_at"])
    record_audit_event(
        tenant=binding.tenant,
        actor=actor,
        request=request,
        action="encryption.kms_disabled",
        target_type="tenant_kms_binding",
        target_id=binding.public_id,
        metadata={"environment": binding.environment, "key_arn": binding.key_arn},
    )
    return binding
