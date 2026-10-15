import hashlib
import json

from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.projects.models import ProjectEnvironment
from apps.templates.models import Template, TemplateStatus
from apps.workflows.models import Workflow
from apps.workflows.serializers import WorkflowSerializer


class WorkflowInstantiationConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "idempotency_conflict"
    default_detail = "This Idempotency-Key conflicts with an earlier request."


def _request_hash(*, template_id, template_version, project_id, name):
    payload = {
        "template_id": template_id,
        "template_version": template_version,
        "project_id": project_id,
        "name": name.strip(),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _replay_instantiation(existing, request_hash):
    if not existing.instantiation_request_hash:
        # Legacy rows did not retain the original request. Editable workflow
        # state cannot establish whether a replay matches that missing evidence.
        raise WorkflowInstantiationConflict(
            "The original request evidence is unavailable for this legacy key. "
            "Retrieve the existing workflow instead of retrying its creation."
        )
    if existing.instantiation_request_hash != request_hash:
        raise WorkflowInstantiationConflict(
            "This Idempotency-Key was already used with a different request."
        )
    return existing, False


@transaction.atomic
def instantiate_workflow_template(
    *, request, project, template, template_version, name, idempotency_key
):
    if not idempotency_key:
        raise serializers.ValidationError(
            {"idempotency_key": "Idempotency-Key is required."}
        )
    if len(idempotency_key) > 255:
        raise serializers.ValidationError(
            {"idempotency_key": "Idempotency-Key must be 255 characters or fewer."}
        )
    request_hash = _request_hash(
        template_id=template.public_id,
        template_version=template_version,
        project_id=project.public_id,
        name=name,
    )
    # Serialize tenant keys before acquiring the shared template counter lock.
    # This order also matches workflow publication and administrator mutations.
    lock_audit_chain(request.user.tenant_id)
    existing = Workflow.objects.filter(
        tenant=request.user.tenant, instantiation_key=idempotency_key
    ).first()
    if existing is not None:
        return _replay_instantiation(existing, request_hash)

    template = Template.objects.select_for_update().get(pk=template.pk)
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

    resolved_name = name.strip() or template.name
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
    organization_already_adopted = Workflow.objects.filter(
        source_template=template,
        tenant__organization_id=request.user.tenant.organization_id,
    ).exists()
    try:
        with transaction.atomic():
            workflow = serializer.save()
            workflow.source_template = template
            workflow.source_template_version = template.version
            workflow.instantiation_key = idempotency_key
            workflow.instantiation_request_hash = request_hash
            workflow.save(
                update_fields=[
                    "source_template",
                    "source_template_version",
                    "instantiation_key",
                    "instantiation_request_hash",
                    "updated_at",
                ]
            )
    except IntegrityError:
        existing = Workflow.objects.filter(
            tenant=request.user.tenant, instantiation_key=idempotency_key
        ).first()
        if existing is not None:
            return _replay_instantiation(existing, request_hash)
        if Workflow.objects.filter(project=project, name=resolved_name).exists():
            raise serializers.ValidationError(
                {"name": "A workflow with this name already exists in the project."}
            ) from None
        raise

    Template.objects.filter(pk=template.pk).update(
        usage_count=F("usage_count") + 1,
        cloned_by_organizations=F("cloned_by_organizations")
        + (0 if organization_already_adopted else 1),
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
