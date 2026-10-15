import hashlib
import json
import re
from graphql import GraphQLError

from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, ValidationError

from apps.audit.services import record_audit_event, lock_audit_chain
from apps.projects.models import ProjectEnvironment
from apps.templates.models import Template, TemplateStatus
from apps.workflows.models import Workflow
from apps.workflows.serializers import WorkflowSerializer, validated_workflow_settings


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
    # Match platform publication's audit-scope-before-template lock order.
    # Counter updates below acquire the template row lock before audit append.
    lock_audit_chain(request.user.tenant_id)
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


def normalized_template_version(version):
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", version) or len(version) > 32:
        raise GraphQLError("Use a numeric template version such as 1.1 or 1.1.0.")
    parts = [int(item) for item in version.split(".")]
    if len(parts) == 3 and parts[2] == 0:
        parts.pop()
    return ".".join(str(item) for item in parts)


def insert_template(**values):
    if not values.get("name", "").strip() or len(values["name"]) > 255:
        raise GraphQLError("Provide a template name of 1 to 255 characters.")
    slug = values["slug"]
    version = normalized_template_version(values["version"])
    values["version"] = version
    if not slug or len(slug) > 255:
        raise GraphQLError(
            "Provide a name that generates a nonempty slug of at most 255 characters."
        )

    def version_exists():
        # Retain legacy rows verbatim while rejecting semantic aliases. All new
        # writers store a canonical value, so the DB uniqueness constraint also
        # protects concurrent canonical/aliased insertion attempts.
        for existing in Template.objects.filter(slug=slug).values_list(
            "version", flat=True
        ):
            try:
                normalized = normalized_template_version(existing)
            except GraphQLError:
                continue
            if normalized == version:
                return True
        return False

    if version_exists():
        raise GraphQLError("A template with this slug and version already exists.")
    try:
        with transaction.atomic():
            return Template.objects.create(**values)
    except IntegrityError:
        if version_exists():
            raise GraphQLError(
                "A template with this slug and version already exists."
            ) from None
        raise


def validate_template_settings(settings):
    if not isinstance(settings, dict):
        raise GraphQLError("Template settings must be an object.")
    if settings.get("consent_template_id"):
        raise GraphQLError(
            "Global templates cannot reference a tenant consent template. Select consent after instantiation."
        )
    try:
        return validated_workflow_settings(settings, tenant=None)
    except ValidationError as exc:
        raise GraphQLError(str(exc.detail)) from None


def require_later_template_version(source, proposed):
    source = normalized_template_version(source)
    proposed = normalized_template_version(proposed)

    def parts(value):
        return tuple(int(item) for item in value.split(".")) + (0,) * (
            3 - len(value.split("."))
        )

    if parts(proposed) <= parts(source):
        raise GraphQLError("The new template version must be later than its source.")
    return proposed
