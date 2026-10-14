from django.db import transaction
from rest_framework import serializers
from apps.verification_policies.models import (
    VerificationPolicy,
    VerificationPolicyStatus,
)
from apps.workflows.models import Workflow, WorkflowStatus, WorkflowVersion
from apps.organizations.models import OrganizationStatus
from apps.verification_policies.serializers import (
    VALID_DOCUMENT_TYPES,
    VerificationPolicyCreateSerializer,
)

SUPPORTED_STEPS = {
    "consent",
    "document",
    "selfie",
    "liveness",
    "face_match",
    "decision",
    "manual_review",
    "webhook",
}
DEFAULT_SETTINGS = {
    "required_document_types": [],
    "required_liveness_level": "passive",
    "face_match_threshold": 0.85,
    "manual_review_threshold": 0.65,
    "verification_expiry_minutes": 1440,
    "media_retention_days": 30,
    "metadata_retention_days": 365,
}


def serialize_workflow(x):
    return {
        "id": x.public_id,
        "project_id": x.project.public_id,
        "name": x.name,
        "description": x.description,
        "status": x.status,
        "steps": x.steps_json,
        "settings": x.settings_json,
        "current_version": x.current_version,
        "source_template_id": (
            x.source_template.public_id if x.source_template_id else None
        ),
        "source_template_version": x.source_template_version,
        "created_at": x.created_at.isoformat(),
        "updated_at": x.updated_at.isoformat(),
    }


class WorkflowSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    steps = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    settings = serializers.JSONField(required=False, default=dict)

    def validate_steps(self, steps):
        invalid = set(steps) - SUPPORTED_STEPS
        if invalid:
            raise serializers.ValidationError(
                f"Unsupported steps: {', '.join(sorted(invalid))}"
            )
        if len(steps) != len(set(steps)):
            raise serializers.ValidationError("Workflow steps cannot be duplicated.")
        if "consent" not in steps or "decision" not in steps:
            raise serializers.ValidationError(
                "Consent and decision steps are required."
            )
        return steps

    def validate_settings(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Workflow settings must be an object.")
        existing = self.instance.settings_json if self.instance is not None else {}
        if not isinstance(existing, dict):
            existing = {}
        tenant = (
            self.instance.tenant
            if self.instance is not None
            else self.context["request"].user.tenant
        )
        return validated_workflow_settings({**existing, **value}, tenant=tenant)

    def validate(self, attrs):
        request = self.context["request"]
        if (
            self.instance is None
            and request.user.tenant.organization.status != OrganizationStatus.ACTIVE
        ):
            if request.user.tenant.workflows.exists():
                raise serializers.ValidationError(
                    {
                        "detail": "Pending workspaces are limited to one draft sandbox workflow."
                    }
                )
            project = request.user.tenant.projects.filter(
                public_id=attrs.get("project_id")
            ).first()
            if project is None or project.environment != "sandbox":
                raise serializers.ValidationError(
                    {
                        "project_id": "Pending workspaces can create workflows only in the sandbox project."
                    }
                )
        return attrs

    def create(self, data):
        request = self.context["request"]
        project = request.user.tenant.projects.get(public_id=data.pop("project_id"))
        return Workflow.objects.create(
            tenant=request.user.tenant,
            project=project,
            created_by=request.user,
            name=data["name"],
            description=data["description"],
            steps_json=data["steps"],
            settings_json={**DEFAULT_SETTINGS, **data["settings"]},
        )

    def update(self, instance, data):
        if instance.status == WorkflowStatus.ARCHIVED:
            raise serializers.ValidationError("Archived workflows cannot be edited.")
        for src, dest in (
            ("name", "name"),
            ("description", "description"),
            ("steps", "steps_json"),
            ("settings", "settings_json"),
        ):
            if src in data:
                setattr(
                    instance,
                    dest,
                    data[src],
                )
        instance.status = WorkflowStatus.DRAFT
        instance.save()
        return instance


class WorkflowPolicySettingsSerializer(VerificationPolicyCreateSerializer):
    required_document_types = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(VALID_DOCUMENT_TYPES)),
        allow_empty=True,
    )
    required_liveness_level = serializers.ChoiceField(choices=["passive", "active"])
    face_match_threshold = serializers.DecimalField(
        max_digits=5, decimal_places=4, min_value=0, max_value=1
    )
    manual_review_threshold = serializers.DecimalField(
        max_digits=5, decimal_places=4, min_value=0, max_value=1
    )
    verification_expiry_minutes = serializers.IntegerField(min_value=1)
    media_retention_days = serializers.IntegerField(min_value=1)
    metadata_retention_days = serializers.IntegerField(min_value=1)
    maker_checker_required = serializers.BooleanField(required=False, default=False)

    def get_fields(self):
        fields = super().get_fields()
        for field in ["name", "description", "project_id"]:
            fields.pop(field)
        return fields


def validated_workflow_settings(settings, *, tenant):
    if not isinstance(settings, dict):
        raise serializers.ValidationError("Workflow settings must be an object.")
    combined = {**DEFAULT_SETTINGS, **settings}
    serializer = WorkflowPolicySettingsSerializer(
        data=combined, context={"tenant": tenant}
    )
    serializer.is_valid(raise_exception=True)
    normalized = dict(serializer.validated_data)
    normalized.pop("consent_template", None)
    for field in [
        "face_match_threshold",
        "manual_review_threshold",
        "document_authenticity_min_confidence",
        "external_risk_review_threshold",
    ]:
        normalized[field] = float(normalized[field])
    return {**combined, **normalized}


@transaction.atomic
def publish_workflow(workflow, user):
    caller_workflow = workflow
    workflow = (
        Workflow.objects.select_for_update(of=("self",))
        .select_related("tenant__organization", "project", "created_by")
        .get(pk=workflow.pk)
    )
    if workflow.status == WorkflowStatus.ARCHIVED:
        raise serializers.ValidationError("Archived workflows cannot be published.")
    if workflow.tenant.organization.status != OrganizationStatus.ACTIVE:
        raise serializers.ValidationError(
            "Workflow publishing is available after platform approval. You can continue editing the sandbox draft."
        )
    steps = WorkflowSerializer().fields["steps"].run_validation(workflow.steps_json)
    WorkflowSerializer().validate_steps(steps)
    settings = validated_workflow_settings(
        workflow.settings_json, tenant=workflow.tenant
    )
    version = workflow.current_version + 1
    creator = user if user.tenant_id == workflow.tenant_id else workflow.created_by
    if creator is not None and creator.tenant_id != workflow.tenant_id:
        creator = None
    policy = VerificationPolicy.objects.create(
        tenant=workflow.tenant,
        project=workflow.project,
        name=f"{workflow.name[:180]} [{workflow.public_id}] workflow policy",
        description=workflow.description,
        version=version,
        status=VerificationPolicyStatus.ACTIVE,
        required_document_types_json=settings["required_document_types"],
        required_liveness_level=settings["required_liveness_level"],
        face_match_threshold=settings["face_match_threshold"],
        manual_review_threshold=settings["manual_review_threshold"],
        verification_expiry_minutes=settings["verification_expiry_minutes"],
        media_retention_days=settings["media_retention_days"],
        metadata_retention_days=settings["metadata_retention_days"],
        maker_checker_required=settings["maker_checker_required"],
        document_authenticity_required=settings["document_authenticity_required"],
        document_authenticity_min_confidence=settings[
            "document_authenticity_min_confidence"
        ],
        document_consistency_rules_json=settings["document_consistency_rules"],
        external_risk_enabled=settings["external_risk_enabled"],
        external_risk_failure_action=settings["external_risk_failure_action"],
        external_risk_review_threshold=settings["external_risk_review_threshold"],
        review_reason_rules_json=settings["review_reason_rules"],
        reuse_rules_json=settings["reuse_rules"],
        default_locale=settings["default_locale"],
        supported_locales_json=settings["supported_locales"],
        consent_template=(
            workflow.tenant.consent_templates.get(
                public_id=settings["consent_template_id"]
            )
            if settings.get("consent_template_id")
            else None
        ),
        created_by=creator,
    )
    result = WorkflowVersion.objects.create(
        workflow=workflow,
        workflow_name=workflow.name,
        version=version,
        steps_json=steps,
        settings_json=settings,
        policy=policy,
        published_by=user,
    )
    workflow.current_version = version
    workflow.status = WorkflowStatus.PUBLISHED
    workflow.save(update_fields=["current_version", "status", "updated_at"])
    caller_workflow.refresh_from_db(fields=["current_version", "status"])
    return result
