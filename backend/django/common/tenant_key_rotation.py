"""Bounded, durable, compare-and-swap tenant ciphertext migration."""

import json
import os

from django.apps import apps
from django.db import connection, transaction
from django.db.models import Max

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.tenants.models import Tenant, TenantDataKey, TenantKeyRotation
from common.fields import (
    EncryptedJSONField,
    PreparedEncryptedValue,
    environment_for_instance,
    tenant_owned_model,
)
from common.tenant_crypto import (
    TENANT_FIELD_VERSION,
    active_key,
    bounded_key_operation,
    decrypt_tenant_json,
    encrypt_tenant_json,
    validate_environment,
    validate_scope,
    wrap_key,
)


@transaction.atomic
def start_rotation(tenant_scope, environment, *, actor=None):
    tenant_scope = validate_scope(tenant_scope)
    environment = validate_environment(environment)
    tenant = Tenant.objects.get(public_id=tenant_scope, deleted_at__isnull=True)
    lock_audit_chain(tenant.pk)
    current = active_key(tenant_scope, environment)
    version = (
        TenantDataKey.objects.filter(
            tenant_scope=tenant_scope, environment=environment
        ).aggregate(value=Max("version"))["value"]
        + 1
    )
    TenantDataKey.objects.filter(pk=current.pk).update(active=False)
    wrapped = wrap_key(tenant_scope, version, os.urandom(32), environment)
    target = TenantDataKey.objects.create(
        tenant_scope=tenant_scope,
        environment=environment,
        version=version,
        active=True,
        wrapped_key_json=wrapped,
        wrapping_provider=wrapped.get("__wrapper", "platform"),
    )
    job = TenantKeyRotation.objects.create(
        tenant_scope=tenant_scope, environment=environment, target_key=target
    )
    record_audit_event(
        tenant=tenant,
        actor=actor,
        action="encryption.rotation_started",
        target_type="tenant_key_rotation",
        target_id=job.public_id,
        metadata={"environment": environment, "target_version": version},
    )
    return job


def rotation_fields():
    result = []
    for model in apps.get_models():
        if not tenant_owned_model(model):
            continue
        for field in model._meta.fields:
            if isinstance(field, EncryptedJSONField) and field.tenant_encryption:
                result.append((f"{model._meta.label_lower}.{field.name}", model, field))
    return sorted(result, key=lambda item: item[0])


def raw_batch(model, field, tenant, after_pk, batch_size):
    quote = connection.ops.quote_name
    indirect = model._meta.label_lower == "providers.providerenvironmentconfiguration"
    owner = (
        model._meta.get_field("provider")
        if indirect
        else (model._meta.pk if model is Tenant else model._meta.get_field("tenant"))
    )
    ownership = f"{quote(owner.column)} = %s"
    if indirect:
        provider = model._meta.get_field("provider").remote_field.model
        tenant_column = quote(provider._meta.get_field("tenant").column)
        ownership = (
            f"{quote(owner.column)} IN (SELECT {quote(provider._meta.pk.column)} "
            f"FROM {quote(provider._meta.db_table)} "
            f"WHERE {tenant_column} = %s)"
        )
    sql = f"SELECT {quote(model._meta.pk.column)}, {quote(field.column)} FROM {quote(model._meta.db_table)} WHERE {ownership} AND {quote(model._meta.pk.column)} > %s ORDER BY {quote(model._meta.pk.column)} LIMIT %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [tenant.pk, after_pk, batch_size])
        return cursor.fetchall()


@bounded_key_operation
@transaction.atomic
def resume_database_batch(job_id, *, batch_size=100):
    if type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError("Rotation batch size must be between 1 and 1000.")
    initial = TenantKeyRotation.objects.get(public_id=job_id)
    tenant = Tenant.objects.get(public_id=initial.tenant_scope)
    lock_audit_chain(tenant.pk)
    job = (
        TenantKeyRotation.objects.select_for_update(no_key=True)
        .select_related("target_key")
        .get(pk=initial.pk)
    )
    if job.status == "completed":
        return job
    if (
        job.target_key.tenant_scope != job.tenant_scope
        or job.target_key.environment != job.environment
        or not job.target_key.active
    ):
        raise ValueError("The rotation target is no longer active.")
    positions = dict(job.positions_json)
    for label, model, field in rotation_fields():
        after = positions.get(label, 0)
        if after == "done":
            continue
        rows = raw_batch(model, field, tenant, after, batch_size)
        if not rows:
            positions[label] = "done"
            continue
        for pk, raw in rows:
            original = json.loads(raw) if isinstance(raw, str) else raw
            instance = model.objects.only("pk").get(pk=pk)
            if (
                original is None
                or environment_for_instance(instance) != job.environment
            ):
                positions[label] = pk
                continue
            if (
                isinstance(original, dict)
                and original.get("__enc__") == TENANT_FIELD_VERSION
                and original.get("kid") == job.target_key.public_id
                and original.get("tenant") == job.tenant_scope
                and original.get("environment") == job.environment
            ):
                positions[label] = pk
                continue
            value = decrypt_tenant_json(
                original,
                tenant_scope=job.tenant_scope,
                environment=job.environment,
                purpose=field.encryption_purpose,
            )
            updated = encrypt_tenant_json(
                value,
                tenant_scope=job.tenant_scope,
                environment=job.environment,
                purpose=field.encryption_purpose,
            )
            changed = model.objects.filter(
                pk=pk, **{field.name: PreparedEncryptedValue(original)}
            ).update(**{field.name: PreparedEncryptedValue(updated)})
            if changed:
                job.migrated_count += 1
            else:
                job.conflict_count += 1
                positions["_pass_conflicts"] = positions.get("_pass_conflicts", 0) + 1
            positions[label] = pk
        job.positions_json = positions
        job.status = "running"
        job.save(
            update_fields=[
                "positions_json",
                "status",
                "migrated_count",
                "conflict_count",
                "updated_at",
            ]
        )
        return job
    job.positions_json = positions
    job.status = "objects_pending"
    job.save(update_fields=["positions_json", "status", "updated_at"])
    return job


@bounded_key_operation
@transaction.atomic
def resume_object_batch(job_id, *, batch_size=25):
    if type(batch_size) is not int or not 1 <= batch_size <= 100:
        raise ValueError("Object rotation batch size must be between 1 and 100.")
    from apps.verifications.models import Verification
    from apps.verifications.evidence import EVIDENCE_OBJECT_ENCRYPTION_PURPOSE
    from common.crypto import (
        decrypt_object_bytes,
        encrypt_object_bytes,
        is_encrypted_object_payload,
    )
    from common.storage import (
        get_object_storage_client,
        get_object_storage_evidence_bucket_name,
        _get_server_side_encryption_params,
    )
    from common.tenant_crypto import TENANT_OBJECT_VERSION

    initial = TenantKeyRotation.objects.get(public_id=job_id)
    tenant = Tenant.objects.get(public_id=initial.tenant_scope)
    lock_audit_chain(tenant.pk)
    job = (
        TenantKeyRotation.objects.select_for_update(no_key=True)
        .select_related("target_key")
        .get(pk=initial.pk)
    )
    if job.status == "completed":
        return job
    if (
        job.status != "objects_pending"
        or not job.target_key.active
        or job.target_key.tenant_scope != job.tenant_scope
        or job.target_key.environment != job.environment
    ):
        raise ValueError("The rotation is not ready for object migration.")
    positions = dict(job.positions_json)
    after = positions.get("objects", 0)
    cases = list(
        Verification.objects.filter(tenant=tenant, pk__gt=after)
        .select_for_update(of=("self",), no_key=True)
        .select_related("tenant", "project")
        .order_by("pk")[:batch_size]
    )
    client = None
    for case in cases:
        if environment_for_instance(case) != job.environment:
            positions["objects"] = case.pk
            continue
        metadata = dict(case.metadata_json or {})
        changed_metadata = False
        for key_field, flag, expected_type in (
            (
                "evidence_report_storage_key",
                "evidence_report_encrypted",
                "application/json",
            ),
            (
                "evidence_report_pdf_storage_key",
                "evidence_report_pdf_encrypted",
                "application/pdf",
            ),
        ):
            key = metadata.get(key_field)
            if not key:
                continue
            from common.tenant_storage import resolve_reference

            bucket = resolve_reference(
                key,
                get_object_storage_evidence_bucket_name(),
                tenant_scope=job.tenant_scope,
                environment=job.environment,
            )["bucket"]
            if not bucket:
                raise ValueError("Evidence storage is unavailable for rotation.")
            if client is None:
                client = get_object_storage_client()
            if client is None:
                raise ValueError("Evidence storage is unavailable for rotation.")
            response = client.get_object(Bucket=bucket, Key=key)
            payload = response["Body"].read(64 * 1024 * 1024 + 1)
            if len(payload) > 64 * 1024 * 1024:
                raise ValueError("Evidence object exceeds the rotation size limit.")
            encoded = is_encrypted_object_payload(payload)
            if metadata.get(flag) and not encoded:
                raise ValueError("Encrypted evidence object is unavailable.")
            if encoded:
                content, content_type = decrypt_object_bytes(
                    payload=payload,
                    purpose=EVIDENCE_OBJECT_ENCRYPTION_PURPOSE,
                    tenant_scope=job.tenant_scope,
                    environment=job.environment,
                )
                envelope = json.loads(payload)
                already_active = (
                    envelope.get("__enc__") == TENANT_OBJECT_VERSION
                    and envelope.get("kid") == job.target_key.public_id
                )
            else:
                content, content_type = payload, response.get(
                    "ContentType", expected_type
                )
                already_active = False
            if content_type != expected_type:
                raise ValueError("Evidence object content type is invalid.")
            if not already_active:
                etag = response.get("ETag")
                if not isinstance(etag, str) or not etag:
                    raise ValueError("Conditional evidence rotation is unavailable.")
                encrypted = encrypt_object_bytes(
                    content=content,
                    content_type=content_type,
                    purpose=EVIDENCE_OBJECT_ENCRYPTION_PURPOSE,
                    tenant_scope=job.tenant_scope,
                    environment=job.environment,
                )
                try:
                    client.put_object(
                        Bucket=bucket,
                        Key=key,
                        Body=encrypted,
                        ContentType="application/vnd.identitycore.encrypted+json",
                        IfMatch=etag,
                        **_get_server_side_encryption_params(),
                    )
                except Exception:
                    raise ValueError(
                        "Conditional evidence rotation failed; retry the batch."
                    ) from None
                job.migrated_count += 1
            if not metadata.get(flag):
                metadata[flag] = True
                changed_metadata = True
        if changed_metadata:
            case.metadata_json = metadata
            case.save(update_fields=["metadata_json", "updated_at"])
        positions["objects"] = case.pk
    if not cases:
        if positions.get("_pass_conflicts", 0):
            positions = {}
            job.status = "running"
        else:
            job.status = "completed"
            record_audit_event(
                tenant=tenant,
                action="encryption.rotation_completed",
                target_type="tenant_key_rotation",
                target_id=job.public_id,
                metadata={
                    "environment": job.environment,
                    "target_version": job.target_key.version,
                    "migrated_count": job.migrated_count,
                    "conflict_count": job.conflict_count,
                },
            )
    job.positions_json = positions
    job.save(update_fields=["positions_json", "status", "migrated_count", "updated_at"])
    return job
