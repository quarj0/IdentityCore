from rest_framework import serializers

from apps.claims.disclosure import CLAIM_CLASSES
from apps.evidence.serializers import StrictInput


class ClaimInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    subject_id = serializers.CharField(max_length=64)
    authorization_id = serializers.CharField(max_length=64)
    schema_id = serializers.CharField(max_length=64)
    observed_at = serializers.DateTimeField()
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    delete_after = serializers.DateTimeField()
    evidence_ids = serializers.ListField(
        child=serializers.CharField(max_length=64),
        max_length=16,
        required=False,
        default=list,
    )
    claim_ids = serializers.ListField(
        child=serializers.CharField(max_length=64),
        max_length=16,
        required=False,
        default=list,
    )
    value = serializers.JSONField(required=False)
    confidence = serializers.DecimalField(
        max_digits=6, decimal_places=5, min_value=0, max_value=1, required=False
    )
    rule_name = serializers.ChoiceField(
        choices=[
            "",
            "copy",
            "field",
            "normalize_name",
            "iso_date",
            "age_over",
            "document_current",
            "exact_corroboration",
        ],
        required=False,
        default="",
    )
    rule_version = serializers.IntegerField(min_value=1, required=False, default=1)
    rule_parameters = serializers.DictField(required=False, default=dict)
    supersedes_id = serializers.CharField(max_length=64, required=False)


class ClaimQuery(serializers.Serializer):
    project_id = serializers.CharField(max_length=64)
    purpose = serializers.CharField(max_length=255)
    include_value = serializers.BooleanField(required=False, default=False)


class ProjectQuery(serializers.Serializer):
    project_id = serializers.CharField(max_length=64)


class ProjectInput(StrictInput):
    project_id = serializers.CharField(max_length=64)


class PolicyInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    schema_id = serializers.CharField(max_length=64)
    name = serializers.SlugField(max_length=120)
    version = serializers.IntegerField(min_value=1)
    purposes = serializers.ListField(
        child=serializers.CharField(max_length=255), min_length=1, max_length=32
    )
    accepted_classes = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(CLAIM_CLASSES)),
        min_length=1,
        max_length=6,
    )
    fields = serializers.ListField(
        child=serializers.CharField(max_length=120), min_length=1, max_length=32
    )
    max_age_seconds = serializers.IntegerField(min_value=1, max_value=366 * 86400)
    minimum_confidence = serializers.DecimalField(
        max_digits=6, decimal_places=5, min_value=0, max_value=1, required=False
    )


class ReviewInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    purpose = serializers.CharField(max_length=255)
    selected_claim_id = serializers.CharField(
        max_length=64, allow_null=True, required=False, default=None
    )
    outcome = serializers.ChoiceField(choices=["selected", "disputed", "more_evidence"])
    reason = serializers.DictField(allow_empty=False)


class RevokeInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    purpose = serializers.CharField(max_length=255)
    reason = serializers.RegexField(r"^[a-z][a-z0-9_]{0,119}$")


class EvaluationInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    purpose = serializers.CharField(max_length=255)
    policy_id = serializers.CharField(max_length=64)


class DisclosureSelection(StrictInput):
    claim_id = serializers.CharField(max_length=64)
    policy_id = serializers.CharField(max_length=64)
    fields = serializers.ListField(
        child=serializers.CharField(max_length=120), min_length=1, max_length=32
    )


class DisclosureInput(StrictInput):
    project_id = serializers.CharField(max_length=64)
    authorization_id = serializers.CharField(max_length=64)
    audience_id = serializers.CharField(max_length=64)
    selections = DisclosureSelection(many=True, min_length=1, max_length=16)
    lifetime_seconds = serializers.IntegerField(
        min_value=1, max_value=900, required=False, default=300
    )
    max_redemptions = serializers.IntegerField(
        min_value=1, max_value=10, required=False, default=1
    )


def policy_summary(record):
    return {
        "id": record.public_id,
        "project_id": record.project.public_id,
        "schema_id": record.schema.public_id,
        "name": record.name,
        "version": record.version,
        "purposes": record.purposes_json,
        "accepted_classes": record.accepted_classes_json,
        "fields": record.disclosure_fields_json,
        "max_age_seconds": record.max_age_seconds,
        "minimum_confidence": str(record.minimum_confidence)
        if record.minimum_confidence is not None
        else None,
        "approved_at": record.approved_at.isoformat() if record.approved_at else None,
        "retired_at": record.retired_at.isoformat() if record.retired_at else None,
    }
