from collections.abc import Mapping

from rest_framework import serializers

from apps.evidence.services import OPERATIONS


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {key: "Unknown field." for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


class EmptyInput(StrictInput):
    pass


class SchemaInput(StrictInput):
    name = serializers.SlugField(max_length=120)
    version = serializers.IntegerField(min_value=1)
    kind = serializers.ChoiceField(choices=["evidence", "claim"])
    definition = serializers.JSONField()
    disclosure_fields = serializers.ListField(
        child=serializers.CharField(max_length=120),
        max_length=100,
        required=False,
        default=list,
    )


class AuthorizationInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    subject_id = serializers.CharField(max_length=64)
    purpose = serializers.CharField(max_length=255)
    legal_basis = serializers.ChoiceField(
        choices=["consent", "contract", "legal_obligation", "legitimate_interest"]
    )
    justification = serializers.JSONField()
    operations = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(OPERATIONS)),
        min_length=1,
        max_length=len(OPERATIONS),
    )
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    delete_after = serializers.DateTimeField(required=False)
    consent_record_id = serializers.CharField(max_length=64, required=False)
    reuse_from_ids = serializers.ListField(
        child=serializers.CharField(max_length=64),
        max_length=16,
        required=False,
        default=list,
    )


class EvidenceInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    subject_id = serializers.CharField(max_length=64)
    authorization_id = serializers.CharField(max_length=64)
    schema_id = serializers.CharField(max_length=64)
    evidence_type = serializers.ChoiceField(
        choices=["submitted", "provider", "system", "human", "authoritative"]
    )
    operation_reference = serializers.CharField(max_length=120)
    payload = serializers.JSONField()
    provenance = serializers.JSONField()
    observed_at = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    delete_after = serializers.DateTimeField()
    source_ids = serializers.ListField(
        child=serializers.CharField(max_length=64),
        max_length=16,
        required=False,
        default=list,
    )
    supersedes_id = serializers.CharField(max_length=64, required=False)
    verification_id = serializers.CharField(max_length=64, required=False)
    source_check_id = serializers.CharField(max_length=64, required=False)


class ResourceQuery(serializers.Serializer):
    project_id = serializers.CharField(max_length=64)
    purpose = serializers.CharField(max_length=255)
    include_payload = serializers.BooleanField(default=False)


class RevokeInput(StrictInput):
    reason = serializers.RegexField(r"^[a-z][a-z0-9_]{0,119}$")


def schema_summary(record):
    return {
        "id": record.public_id,
        "name": record.name,
        "version": record.version,
        "kind": record.kind,
        "definition": record.definition_json,
        "disclosure_fields": record.disclosure_fields_json,
        "retired_at": record.retired_at.isoformat() if record.retired_at else None,
    }


def authorization_summary(record):
    return {
        "id": record.public_id,
        "project_id": record.project.public_id,
        "subject_id": record.subject.public_id,
        "purpose": record.purpose,
        "legal_basis": record.legal_basis,
        "operations": record.allowed_operations_json,
        "approved_at": record.approved_at.isoformat() if record.approved_at else None,
        "valid_from": record.valid_from.isoformat(),
        "valid_until": record.valid_until.isoformat(),
        "delete_after": record.delete_after.isoformat(),
        "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None,
        "reuse_from_ids": list(
            record.reuse_sources.values_list(
                "source_authorization__public_id", flat=True
            )
        ),
    }


class HoldInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    subject_id = serializers.CharField(max_length=64)
    reason = serializers.DictField(allow_empty=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


def hold_summary(record):
    return {
        "id": record.public_id,
        "project_id": record.project.public_id,
        "subject_id": record.subject.public_id,
        "created_at": record.created_at.isoformat(),
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "released_at": record.released_at.isoformat() if record.released_at else None,
        "scope": "subject_project_lineage",
    }
