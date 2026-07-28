import hashlib
import json

from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from apps.audit.services import record_audit_event
from apps.projects.models import ProjectEnvironment
from apps.templates.models import Template, TemplateStatus
from apps.workflows.models import Workflow
from apps.workflows.serializers import WorkflowSerializer


class WorkflowInstantiationConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "idempotency_conflict"
    default_detail = "This Idempotency-Key conflicts with an earlier request."


def _request_hash(*, template, project, name):
    payload = {
        "template_id": template.public_id,
        "template_version": template.version,
        "project_id": project.public_id,
        "name": name,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@transaction.atomic
def instantiate_workflow_template(
    *, request, project, template, template_version, name, idempotency_key
):
    if template.status != TemplateStatus.PUBLISHED:
        raise serializers.ValidationError(
            {"template_id": "Only published workflow templates can be instantiated."}
        )
    if template.version != template_version:
        raise serializers.ValidationError(
            {"template_version": "The requested template version is not available."}
        )
    if (
        project.environment != ProjectEnvironment.SANDBOX
        and request.user.tenant.organization.status != "active"
    ):
        raise serializers.ValidationError(
            {"project_id": "Production projects require an approved organization."}
        )
    if not idempotency_key:
        raise serializers.ValidationError(
            {"idempotency_key": "Idempotency-Key is required."}
        )
    if len(idempotency_key) > 255:
        raise serializers.ValidationError(
            {"idempotency_key": "Idempotency-Key must be 255 characters or fewer."}
        )

    resolved_name = name.strip() or template.name
    request_hash = _request_hash(
        template=template,
        project=project,
        name=resolved_name,
    )
    existing = (
        Workflow.objects.filter(
            tenant=request.user.tenant,
            instantiation_key=idempotency_key,
        )
        .select_related("project", "source_template")
        .first()
    )
    if existing is not None:
        existing_hash = _request_hash(
            template=existing.source_template,
            project=existing.project,
            name=existing.name,
        )
        if existing_hash != request_hash:
            raise WorkflowInstantiationConflict(
                "This Idempotency-Key was already used with a different request."
            )
        return existing, False

    serializer = WorkflowSerializer(
        data={
            "project_id": project.public_id,
            "name": resolved_name,
            "description": template.description,
            "steps": template.steps_json,
            "settings": template.settings_json,
        },
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            workflow = serializer.save()
            workflow.source_template = template
            workflow.source_template_version = template.version
            workflow.instantiation_key = idempotency_key
            workflow.save(
                update_fields=[
                    "source_template",
                    "source_template_version",
                    "instantiation_key",
                    "updated_at",
                ]
            )
    except IntegrityError:
        existing = Workflow.objects.get(
            tenant=request.user.tenant,
            instantiation_key=idempotency_key,
        )
        return existing, False

    Template.objects.filter(pk=template.pk).update(
        usage_count=F("usage_count") + 1,
        cloned_by_organizations=F("cloned_by_organizations") + 1,
    )
    record_audit_event(
        tenant=request.user.tenant,
        actor=request.user,
        request=request,
        action="workflow.template_instantiated",
        target_type="workflow",
        target_id=workflow.public_id,
        metadata={
            "template_id": template.public_id,
            "template_version": template.version,
            "project_id": project.public_id,
        },
    )
    return workflow, True
