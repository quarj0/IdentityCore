from django.db import transaction
from rest_framework import serializers
from apps.verification_policies.models import (
    VerificationPolicy,
    VerificationPolicyStatus,
)
from apps.workflows.models import Workflow, WorkflowStatus, WorkflowVersion

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
                    (
                        data[src]
                        if src != "settings"
                        else {**instance.settings_json, **data[src]}
                    ),
                )
        instance.status = WorkflowStatus.DRAFT
        instance.save()
        return instance


@transaction.atomic
def publish_workflow(workflow, user):
    version = workflow.current_version + 1
    s = {**DEFAULT_SETTINGS, **workflow.settings_json}
    policy = VerificationPolicy.objects.create(
        tenant=workflow.tenant,
        project=workflow.project,
        name=workflow.name,
        description=workflow.description,
        version=version,
        status=VerificationPolicyStatus.ACTIVE,
        required_document_types_json=s["required_document_types"],
        required_liveness_level=s["required_liveness_level"],
        face_match_threshold=s["face_match_threshold"],
        manual_review_threshold=s["manual_review_threshold"],
        verification_expiry_minutes=s["verification_expiry_minutes"],
        media_retention_days=s["media_retention_days"],
        metadata_retention_days=s["metadata_retention_days"],
        created_by=user,
    )
    result = WorkflowVersion.objects.create(
        workflow=workflow,
        version=version,
        steps_json=workflow.steps_json,
        settings_json=s,
        policy=policy,
        published_by=user,
    )
    workflow.current_version = version
    workflow.status = WorkflowStatus.PUBLISHED
    workflow.save(update_fields=["current_version", "status", "updated_at"])
    return result
