from __future__ import annotations

from dataclasses import dataclass

from django.db import models
from django.db.models.query_utils import DeferredAttribute

from common.crypto import decrypt_json_value, encrypt_json_value
from common.tenant_crypto import (
    TENANT_FIELD_VERSION,
    decrypt_tenant_json,
    encrypt_tenant_json,
)


@dataclass(frozen=True)
class PreparedEncryptedValue:
    envelope: dict


@dataclass(frozen=True)
class StoredTenantEnvelope:
    """Raw query results cannot decrypt without an expected owning instance."""

    envelope: dict


def tenant_scope_for_instance(instance):
    if instance._meta.label_lower == "tenants.tenant":
        if not getattr(instance, "public_id", None):
            instance.ensure_public_id()
        return instance.public_id
    if getattr(instance, "tenant_id", None) is not None:
        return instance.tenant.public_id
    return None


def environment_for_instance(instance, depth=0):
    if depth > 4:
        raise ValueError("Encryption environment could not be established.")
    if instance._meta.label_lower == "projects.project":
        return instance.environment
    if getattr(instance, "project_id", None) is not None:
        return instance.project.environment
    for relation in (
        "verification",
        "identity_document",
        "verification_session",
        "capture_session",
    ):
        if getattr(instance, relation + "_id", None) is not None:
            return environment_for_instance(getattr(instance, relation), depth + 1)
    if instance._meta.label_lower == "verifications.verification":
        return "sandbox"
    return "shared"


def tenant_owned_model(model):
    return model._meta.label_lower == "tenants.tenant" or any(
        field.name == "tenant" for field in model._meta.fields
    )


class TenantEncryptedAttribute(DeferredAttribute):
    def __set__(self, instance, value):
        instance.__dict__[self.field.attname] = value

    def __get__(self, instance, cls=None):
        value = super().__get__(instance, cls)
        if instance is not None and isinstance(value, StoredTenantEnvelope):
            scope = tenant_scope_for_instance(instance)
            if scope is None:
                raise ValueError("Tenant encrypted content is unavailable.")
            value = decrypt_tenant_json(
                value.envelope,
                tenant_scope=scope,
                purpose=self.field.encryption_purpose,
                environment=environment_for_instance(instance),
            )
            instance.__dict__[self.field.attname] = value
        return value


class EncryptedJSONField(models.JSONField):
    descriptor_class = TenantEncryptedAttribute

    def __init__(self, *args, encryption_purpose: str, **kwargs):
        self.encryption_purpose = encryption_purpose
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["encryption_purpose"] = self.encryption_purpose
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if value is None:
            return None
        # Historical migrations must not query key tables that did not exist yet.
        historical = model_instance.__class__.__module__ == "__fake__"
        scope = None if historical else tenant_scope_for_instance(model_instance)
        envelope = (
            encrypt_tenant_json(
                value,
                tenant_scope=scope,
                purpose=self.encryption_purpose,
                environment=environment_for_instance(model_instance),
            )
            if scope
            else encrypt_json_value(value, purpose=self.encryption_purpose)
        )
        return PreparedEncryptedValue(envelope)

    def get_prep_value(self, value):
        if isinstance(value, PreparedEncryptedValue):
            return value.envelope
        if isinstance(value, StoredTenantEnvelope):
            raise ValueError("Tenant encrypted queries require ownership context.")
        prepared = super().get_prep_value(value)
        if prepared is None:
            return None
        if tenant_owned_model(self.model) and self.model.__module__ != "__fake__":
            raise ValueError(
                "Tenant encrypted writes require an owning model instance."
            )
        return encrypt_json_value(prepared, purpose=self.encryption_purpose)

    def from_db_value(self, value, expression, connection):
        decoded = super().from_db_value(value, expression, connection)
        if isinstance(decoded, dict) and decoded.get("__enc__") == TENANT_FIELD_VERSION:
            return StoredTenantEnvelope(decoded)
        return decrypt_json_value(decoded, purpose=self.encryption_purpose)

    def to_python(self, value):
        # Incoming dictionaries are plaintext input; only database conversion may
        # mark an envelope for instance-bound decryption.
        if isinstance(value, (PreparedEncryptedValue, StoredTenantEnvelope)):
            return value
        return super().to_python(value)
