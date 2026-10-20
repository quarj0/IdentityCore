"""Audited evidence creation and explicit purpose-authorization lifecycle."""

from django.db import models, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.evidence.access import (
    current_actor,
    identity,
    require_authorization,
    protected_value,
)
from apps.evidence.models import (
    AuthorizationReuse,
    Evidence,
    EvidenceSource,
    PurposeAuthorization,
    ResourceSchema,
)
from apps.evidence.validation import (
    canonical_json,
    digest,
    validate_payload,
    validate_schema,
)
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject

OPERATIONS = {
    "evidence:read",
    "evidence:write",
    "claims:read",
    "claims:write",
    "claims:disclose",
}
MAX_SOURCES = 16
MAX_LINEAGE_NODES = 256
MAX_LINEAGE_DEPTH = 32


def _transition(instance, **fields):
    """Internal persistence primitive; callers must hold the tenant audit lock."""
    for name, value in fields.items():
        setattr(instance, name, value)
    models.Model.save(instance, update_fields=[*fields, "updated_at"])


def _scope(
    tenant_id,
    project_id=None,
    subject_id=None,
    *,
    allow_inactive_project=False,
    allow_restricted_subject=False,
):
    lock_audit_chain(tenant_id)
    tenant = Tenant.objects.get(pk=tenant_id)
    project = None
    subject = None
    if project_id is not None:
        projects = Project.objects.filter(tenant=tenant, public_id=project_id)
        if not allow_inactive_project:
            projects = projects.filter(deleted_at__isnull=True, status="active")
        project = projects.first()
        if project is None:
            raise NotFound()
    if subject_id is not None:
        subject = VerificationSubject.objects.filter(
            tenant=tenant, public_id=subject_id, deleted_at__isnull=True
        ).first()
        if subject is None:
            raise NotFound()
        from apps.evidence.models import SubjectResourceRestriction

        if (
            not allow_restricted_subject
            and SubjectResourceRestriction.objects.filter(
                subject=subject, tenant=tenant
            ).exists()
        ):
            raise NotFound()
    return tenant, project, subject


def _audit(resource, actor, action, request=None, **metadata):
    return record_audit_event(
        tenant_id=resource.tenant_id,
        actor=actor,
        action=action,
        target_type=resource._meta.model_name,
        target_id=resource.public_id,
        request=request,
        metadata=metadata,
    )


@transaction.atomic
def create_schema(
    *,
    tenant_id,
    actor,
    name,
    version,
    kind,
    definition,
    disclosure_fields=(),
    request=None,
):
    tenant, _, _ = _scope(tenant_id)
    actor = current_actor(actor, tenant, "schemas:write")
    validate_schema(definition)
    if kind not in {"evidence", "claim"}:
        raise ValidationError("Choose evidence or claim schema.")
    if (
        not isinstance(disclosure_fields, (list, tuple))
        or len(disclosure_fields) != len(set(disclosure_fields))
        or any(
            not isinstance(field, str) or field not in definition.get("properties", {})
            for field in disclosure_fields
        )
    ):
        raise ValidationError("Disclosure fields must name distinct schema properties.")
    record = ResourceSchema.objects.create(
        tenant=tenant,
        name=name,
        version=version,
        kind=kind,
        definition_json=definition,
        disclosure_fields_json=list(disclosure_fields),
        created_by_id_snapshot=identity(actor),
    )
    _audit(record, actor, "evidence.schema_created", request)
    return record


def _require_reuse_source(source):
    # Reusable claims may have no underlying evidence permission on their grant.
    operation = next(
        (
            name
            for name in ("evidence:read", "claims:read")
            if name in source.allowed_operations_json
        ),
        None,
    )
    if operation is None:
        raise PermissionDenied("Source authorization does not permit resource reads.")
    return require_authorization(source, operation=operation)


@transaction.atomic
def propose_authorization(
    *,
    tenant_id,
    actor,
    project_id,
    subject_id,
    purpose,
    legal_basis,
    justification,
    operations,
    valid_from,
    valid_until,
    consent_record_id=None,
    reuse_from_ids=(),
    delete_after=None,
    request=None,
):
    tenant, project, subject = _scope(tenant_id, project_id, subject_id)
    actor = current_actor(actor, tenant, "authorizations:write", project=project)
    canonical_json(justification, maximum=32 * 1024)
    if not isinstance(justification, dict) or not justification:
        raise ValidationError("A documented legal-basis justification is required.")
    if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 255:
        raise ValidationError("An explicit bounded purpose is required.")
    if (
        not isinstance(operations, list)
        or not operations
        or any(not isinstance(op, str) or op not in OPERATIONS for op in operations)
        or len(operations) != len(set(operations))
    ):
        raise ValidationError("Choose distinct supported purpose operations.")
    if (
        timezone.is_naive(valid_from)
        or timezone.is_naive(valid_until)
        or valid_until <= valid_from
        or valid_until <= timezone.now()
    ):
        raise ValidationError(
            "Choose an aware, nonempty authorization validity interval."
        )
    if (
        not isinstance(reuse_from_ids, (list, tuple))
        or len(reuse_from_ids) > MAX_SOURCES
        or any(not isinstance(x, str) for x in reuse_from_ids)
        or len(set(reuse_from_ids)) != len(reuse_from_ids)
    ):
        raise ValidationError("Choose distinct bounded source authorizations.")
    reuse_sources = list(
        PurposeAuthorization.objects.select_related(
            "tenant", "project", "subject", "consent_record__verification"
        ).filter(
            tenant=tenant,
            project=project,
            subject=subject,
            public_id__in=reuse_from_ids,
        )
    )
    if len(reuse_sources) != len(reuse_from_ids):
        raise NotFound()
    for source in reuse_sources:
        _require_reuse_source(source)
    delete_after = valid_until if delete_after is None else delete_after
    if timezone.is_naive(delete_after) or delete_after < valid_until:
        raise ValidationError("Authorization retention must cover its validity.")
    consent = None
    if consent_record_id:
        from apps.consent.models import ConsentRecord

        consent = ConsentRecord.objects.filter(
            public_id=consent_record_id,
            tenant=tenant,
            verification_subject=subject,
            verification__project=project,
        ).first()
        if consent is None:
            raise NotFound()
    if legal_basis == "consent" and consent is None:
        raise ValidationError(
            "Consent authorization must reference its accepted proof."
        )
    if legal_basis != "consent" and consent is not None:
        raise ValidationError(
            "A consent reference cannot establish another legal basis."
        )
    record = PurposeAuthorization.objects.create(
        tenant=tenant,
        project=project,
        subject=subject,
        purpose=purpose.strip(),
        legal_basis=legal_basis,
        justification_json=justification,
        consent_record=consent,
        allowed_operations_json=operations,
        proposed_by_id_snapshot=identity(actor),
        valid_from=valid_from,
        valid_until=valid_until,
        delete_after=delete_after,
    )
    for source in reuse_sources:
        AuthorizationReuse.objects.create(
            authorization=record, source_authorization=source
        )
    if legal_basis == "consent" and not reuse_sources:
        # Only current, exact-purpose proof can activate without a second officer.
        record.approved_at = timezone.now()
        record.approved_by_id_snapshot = identity(actor)
        require_authorization(record, operation=operations[0])
        _transition(
            record,
            approved_at=record.approved_at,
            approved_by_id_snapshot=record.approved_by_id_snapshot,
        )
    _audit(
        record,
        actor,
        "evidence.authorization_proposed",
        request,
        legal_basis=legal_basis,
    )
    return record


@transaction.atomic
def approve_authorization(*, tenant_id, actor, authorization_id, request=None):
    tenant, _, _ = _scope(tenant_id)
    actor = current_actor(actor, tenant, "authorizations:approve")
    record = (
        PurposeAuthorization.objects.select_related(
            "tenant", "project", "subject", "consent_record"
        )
        .filter(tenant=tenant, public_id=authorization_id)
        .first()
    )
    if record is None:
        raise NotFound()
    if record.proposed_by_id_snapshot == identity(actor):
        raise PermissionDenied(
            "A different privacy officer must approve this authorization."
        )
    if record.revoked_at or record.deleted_at or record.valid_until <= timezone.now():
        raise ValidationError("The purpose authorization is unavailable.")
    if (
        record.subject.deleted_at
        or record.project.deleted_at
        or record.project.status != "active"
    ):
        raise ValidationError("The authorization context is inactive.")
    for edge in record.reuse_sources.select_related(
        "source_authorization__tenant",
        "source_authorization__project",
        "source_authorization__subject",
        "source_authorization__consent_record__verification",
    ):
        _require_reuse_source(edge.source_authorization)
    # Validate the live context and exact consent proof before persisting approval.
    # Future grants can be approved now, but cannot be used before valid_from.
    if not record.approved_at:
        record.approved_at = timezone.now()
        record.approved_by_id_snapshot = identity(actor)
    require_authorization(
        record,
        operation=record.allowed_operations_json[0],
        at=max(timezone.now(), record.valid_from),
    )
    if not PurposeAuthorization.objects.get(pk=record.pk).approved_at:
        _transition(
            record,
            approved_at=record.approved_at,
            approved_by_id_snapshot=record.approved_by_id_snapshot,
        )
        _audit(record, actor, "evidence.authorization_approved", request)
    return record


def _authorization(tenant, project, subject, public_id, operation):
    record = (
        PurposeAuthorization.objects.select_related(
            "tenant", "project", "subject", "consent_record__verification"
        )
        .filter(tenant=tenant, project=project, subject=subject, public_id=public_id)
        .first()
    )
    if record is None:
        raise NotFound()
    return require_authorization(record, operation=operation)


def _local_active(record, now, validated_authorizations):
    if (
        record.deleted_at
        or record.status != "active"
        or now >= record.valid_until
        or now >= record.delete_after
    ):
        raise PermissionDenied("Supporting evidence is unavailable.")
    if record.source_check_id:
        check = record.source_check
        if (
            check.deleted_at
            or check.status != "completed"
            or digest(protected_value(check, "normalized_result_json"))
            != record.payload_sha256
        ):
            raise PermissionDenied("The provider evidence source is unavailable.")
    if record.authorization_id not in validated_authorizations:
        require_authorization(record.authorization, operation="evidence:read", at=now)
        validated_authorizations.add(record.authorization_id)


def ancestry(record, *, validate_active=True):
    """Load all ancestors with explicit bounds; never silently omit dependencies."""
    found = {record.pk: record}
    frontier = [record]
    now = timezone.now()
    depth = 0
    validated_authorizations = set()
    while frontier:
        if depth > MAX_LINEAGE_DEPTH:
            raise ValidationError("Evidence lineage exceeds the supported depth.")
        if validate_active:
            for item in frontier:
                _local_active(item, now, validated_authorizations)
        parent_ids = set(
            EvidenceSource.objects.filter(
                evidence_id__in=[item.pk for item in frontier]
            ).values_list("source_id", flat=True)
        ) - set(found)
        if not parent_ids:
            break
        if len(found) + len(parent_ids) > MAX_LINEAGE_NODES:
            raise ValidationError("Evidence lineage exceeds the supported node limit.")
        frontier = list(
            Evidence.objects.select_related(
                "tenant",
                "project",
                "subject",
                "authorization__tenant",
                "authorization__project",
                "authorization__subject",
                "authorization__consent_record__verification",
            ).filter(pk__in=parent_ids)
        )
        if len(frontier) != len(parent_ids):
            raise PermissionDenied("Evidence provenance is unavailable.")
        for item in frontier:
            if (item.tenant_id, item.project_id, item.subject_id, item.purpose) != (
                record.tenant_id,
                record.project_id,
                record.subject_id,
                record.purpose,
            ):
                raise PermissionDenied("Evidence provenance is unavailable.")
            found[item.pk] = item
        depth += 1
    return found


@transaction.atomic
def create_evidence(
    *,
    tenant_id,
    actor,
    project_id,
    subject_id,
    authorization_id,
    schema_id,
    evidence_type,
    operation_reference,
    payload,
    provenance,
    observed_at,
    valid_until,
    delete_after,
    source_ids=(),
    supersedes_id=None,
    verification_id=None,
    source_check_id=None,
    request=None,
):
    tenant, project, subject = _scope(tenant_id, project_id, subject_id)
    actor = current_actor(actor, tenant, "evidence:write", project=project)
    auth = _authorization(tenant, project, subject, authorization_id, "evidence:write")
    if (
        not isinstance(source_ids, (list, tuple))
        or len(source_ids) > MAX_SOURCES
        or len(source_ids) != len(set(source_ids))
        or any(not isinstance(x, str) for x in source_ids)
    ):
        raise ValidationError("Choose distinct, bounded evidence sources.")
    now = timezone.now()
    if (
        any(
            timezone.is_naive(value)
            for value in (observed_at, valid_until, delete_after)
        )
        or observed_at > now
        or valid_until <= now
        or delete_after < valid_until
        or valid_until > auth.valid_until
    ):
        raise ValidationError(
            "Evidence validity must fit its authorization and retention interval."
        )
    schema = ResourceSchema.objects.filter(
        tenant=tenant, public_id=schema_id, kind="evidence", retired_at__isnull=True
    ).first()
    if schema is None:
        raise NotFound()
    payload_hash = validate_payload(schema, payload)
    canonical_json(provenance, maximum=32 * 1024)
    if not isinstance(provenance, dict) or not provenance:
        raise ValidationError("Explicit evidence provenance is required.")
    sources = list(
        Evidence.objects.select_related(
            "authorization__tenant",
            "authorization__project",
            "authorization__subject",
            "authorization__consent_record__verification",
        ).filter(
            tenant=tenant,
            project=project,
            subject=subject,
            purpose=auth.purpose,
            public_id__in=source_ids,
        )
    )
    if len(sources) != len(source_ids):
        raise NotFound()
    ancestors = set()
    for parent in sources:
        ancestors.update(ancestry(parent))
        if valid_until > parent.valid_until or delete_after > parent.delete_after:
            raise ValidationError("Derived evidence cannot outlive its sources.")
    if len(ancestors) >= MAX_LINEAGE_NODES:
        raise ValidationError("Evidence lineage exceeds the supported node limit.")
    old = None
    if supersedes_id:
        old = Evidence.objects.filter(
            tenant=tenant,
            project=project,
            subject=subject,
            purpose=auth.purpose,
            public_id=supersedes_id,
            status="active",
        ).first()
        if old is None:
            raise NotFound()
        if old.pk in ancestors:
            raise ValidationError(
                "A correction cannot depend on the record it supersedes."
            )
    verification = None
    if verification_id:
        from apps.verifications.models import Verification

        verification = Verification.objects.filter(
            tenant=tenant,
            project=project,
            verification_subject=subject,
            public_id=verification_id,
            purpose=auth.purpose,
            deleted_at__isnull=True,
        ).first()
        if verification is None:
            raise NotFound()
    source_check = None
    if source_check_id:
        from apps.providers.models import ProviderCheck
        from apps.providers.adapters import (
            normalize_provider_result,
            ProviderContractError,
        )

        source_check = (
            ProviderCheck.objects.select_related("provider", "verification")
            .filter(
                tenant=tenant,
                verification=verification,
                public_id=source_check_id,
                status="completed",
                deleted_at__isnull=True,
            )
            .first()
        )
        if source_check is None:
            raise NotFound()
        if evidence_type != "provider":
            raise ValidationError("Provider check evidence must declare provider type.")
        try:
            normalized = normalize_provider_result(
                source_check.check_type,
                protected_value(source_check, "normalized_result_json"),
            )
        except ProviderContractError as exc:
            raise ValidationError(
                "The provider check has no valid normalized result."
            ) from exc
        if digest(protected_value(source_check, "normalized_result_json")) != digest(
            normalized
        ):
            raise ValidationError(
                "Legacy provider checks require an explicit reviewed mapping."
            )
        if digest(normalized) != payload_hash:
            raise ValidationError(
                "Provider evidence must preserve the exact normalized check result."
            )
        provenance = {
            **provenance,
            "provider_id": source_check.provider.public_id,
            "provider_check_id": source_check.public_id,
            "capability": source_check.check_type,
            "contract_version": normalized["contract_version"],
            "origin": "persisted_provider_check",
        }
    record = Evidence.objects.create(
        source_check=source_check,
        tenant=tenant,
        project=project,
        subject=subject,
        authorization=auth,
        schema=schema,
        verification=verification,
        operation_reference=operation_reference,
        purpose=auth.purpose,
        evidence_type=evidence_type,
        payload_json=payload,
        provenance_json=provenance,
        payload_sha256=payload_hash,
        provenance_sha256=digest(provenance),
        observed_at=observed_at,
        valid_until=valid_until,
        delete_after=delete_after,
        supersedes=old,
        created_by_id_snapshot=identity(actor),
    )
    for parent in sources:
        EvidenceSource.objects.create(evidence=record, source=parent)
    ancestry(record, validate_active=False)
    if old is not None:
        invalidate_evidence_tree(
            old, reason="superseded", status="superseded", actor=actor, request=request
        )
    _audit(
        record,
        actor,
        "evidence.created",
        request,
        schema_id=schema.public_id,
        source_count=len(sources),
    )
    return record


def invalidate_evidence_tree(
    record, *, reason, status="revoked", actor=None, request=None
):
    """Internal lifecycle propagation; the caller holds the tenant audit lock."""
    now = timezone.now()
    frontier = {record.pk}
    seen = set()
    while frontier:
        batch = sorted(frontier - seen)
        if not batch:
            break
        seen.update(batch)
        for item in Evidence.objects.filter(
            tenant_id=record.tenant_id, pk__in=batch
        ).select_related("tenant", "project"):
            if item.status == "active":
                _transition(
                    item,
                    status=status if item.pk == record.pk else "revoked",
                    invalidated_at=now,
                    invalidation_reason=reason,
                )
                _audit(item, actor, "evidence.invalidated", request, reason=reason)
        from apps.claims.models import Claim
        from apps.claims.services import invalidate_claim_tree

        for claim in (
            Claim.objects.filter(
                tenant_id=record.tenant_id,
                evidence_edges__evidence_id__in=batch,
                status="active",
            )
            .distinct()
            .iterator(chunk_size=100)
        ):
            invalidate_claim_tree(claim, reason=reason, actor=actor, request=request)
        frontier = (
            set(
                EvidenceSource.objects.filter(
                    source_id__in=batch, evidence__tenant_id=record.tenant_id
                ).values_list("evidence_id", flat=True)
            )
            - seen
        )
    return seen


@transaction.atomic
def read_evidence(
    *,
    tenant_id,
    actor,
    project_id,
    evidence_id,
    purpose,
    include_payload=False,
    request=None,
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "evidence:read", project=project)
    record = (
        Evidence.objects.select_related(
            "schema",
            "tenant",
            "project",
            "subject",
            "authorization__tenant",
            "authorization__project",
            "authorization__subject",
            "authorization__consent_record__verification",
        )
        .filter(tenant=tenant, project=project, public_id=evidence_id, purpose=purpose)
        .first()
    )
    if record is None:
        raise NotFound()
    ancestry(record)
    payload = {
        "id": record.public_id,
        "schema_id": record.schema.public_id,
        "schema_version": record.schema.version,
        "subject_id": record.subject.public_id,
        "project_id": project.public_id,
        "purpose": record.purpose,
        "evidence_type": record.evidence_type,
        "origin": "persisted_provider_check"
        if record.source_check_id
        else "caller_asserted",
        "status": record.status,
        "observed_at": record.observed_at.isoformat(),
        "valid_until": record.valid_until.isoformat(),
        "delete_after": record.delete_after.isoformat(),
        "source_evidence_ids": list(record.sources.values_list("public_id", flat=True)),
        "supersedes_id": record.supersedes.public_id if record.supersedes_id else None,
    }
    if include_payload:
        import hmac

        if not hmac.compare_digest(
            digest(protected_value(record, "payload_json")), record.payload_sha256
        ) or not hmac.compare_digest(
            digest(protected_value(record, "provenance_json")), record.provenance_sha256
        ):
            raise PermissionDenied("Evidence integrity could not be verified.")
        payload["payload"] = protected_value(record, "payload_json")
        payload["provenance"] = protected_value(record, "provenance_json")
    _audit(
        record, actor, "evidence.accessed", request, payload_included=include_payload
    )
    return payload


@transaction.atomic
def revoke_authorization(*, tenant_id, actor, authorization_id, reason, request=None):
    tenant, _, _ = _scope(tenant_id)
    actor = current_actor(actor, tenant, "authorizations:write")
    record = PurposeAuthorization.objects.filter(
        tenant=tenant, public_id=authorization_id
    ).first()
    if record is None:
        raise NotFound()
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 120:
        raise ValidationError("A bounded revocation reason code is required.")
    if record.revoked_at:
        return record
    _transition(record, revoked_at=timezone.now(), revocation_reason=reason)
    _audit(record, actor, "evidence.authorization_revoked", request, reason=reason)
    for evidence in Evidence.objects.filter(
        authorization=record, status="active"
    ).iterator(chunk_size=100):
        invalidate_evidence_tree(
            evidence, reason="authorization_revoked", actor=actor, request=request
        )
    return record


@transaction.atomic
def revoke_evidence(
    *, tenant_id, actor, project_id, evidence_id, purpose, reason, request=None
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "evidence:write", project=project)
    record = Evidence.objects.filter(
        tenant=tenant, project=project, purpose=purpose, public_id=evidence_id
    ).first()
    if record is None:
        raise NotFound()
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 120:
        raise ValidationError("A bounded revocation reason code is required.")
    invalidate_evidence_tree(record, reason=reason, actor=actor, request=request)
    return record


@transaction.atomic
def retire_schema(*, tenant_id, actor, schema_id, request=None):
    tenant, _, _ = _scope(tenant_id)
    actor = current_actor(actor, tenant, "schemas:write")
    record = ResourceSchema.objects.filter(tenant=tenant, public_id=schema_id).first()
    if record is None:
        raise NotFound()
    if record.retired_at is None:
        _transition(record, retired_at=timezone.now())
        _audit(record, actor, "evidence.schema_retired", request)
    return record
