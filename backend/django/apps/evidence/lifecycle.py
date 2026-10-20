"""Privacy, hold and retention operations shared by every governed workload."""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.audit.services import lock_audit_chain
from apps.evidence.access import current_actor, identity
from apps.evidence.models import Evidence, PurposeAuthorization, ResourceLegalHold
from apps.evidence.services import _audit, _scope, _transition, invalidate_evidence_tree
from apps.evidence.validation import canonical_json
from apps.tenants.models import Tenant
from apps.verifications.models import RetentionLegalHold


def active_subject_holds(subject, project=None, *, now=None, include_legacy=True):
    now = now or timezone.now()
    active = Q(released_at__isnull=True) & (
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    governed = ResourceLegalHold.objects.filter(
        active, tenant_id=subject.tenant_id, subject=subject
    )
    if project is not None:
        governed = governed.filter(project=project)
    result = list(governed.values_list("public_id", flat=True))
    if not include_legacy:
        return result
    legacy_scope = Q(tenant_id=subject.tenant_id, verification__isnull=True) | Q(
        verification__verification_subject=subject
    )
    legacy = RetentionLegalHold.objects.filter(active).filter(legacy_scope)
    if project is not None:
        legacy = legacy.filter(
            Q(verification__isnull=True) | Q(verification__project=project)
        )
    return result + list(legacy.values_list("public_id", flat=True))


@transaction.atomic
def create_legal_hold(
    *, tenant_id, actor, project_id, subject_id, reason, expires_at=None, request=None
):
    tenant, project, subject = _scope(
        tenant_id,
        project_id,
        subject_id,
        allow_inactive_project=True,
        allow_restricted_subject=True,
    )
    actor = current_actor(actor, tenant, "authorizations:write", project=project)
    canonical_json(reason, maximum=32 * 1024)
    if not isinstance(reason, dict) or not reason:
        raise ValidationError("A documented hold reason is required.")
    if expires_at is not None and (
        timezone.is_naive(expires_at) or expires_at <= timezone.now()
    ):
        raise ValidationError("Hold expiry must be an aware future timestamp.")
    hold = ResourceLegalHold.objects.create(
        tenant=tenant,
        project=project,
        subject=subject,
        reason_json=reason,
        created_by_id_snapshot=identity(actor),
        expires_at=expires_at,
    )
    _audit(hold, actor, "evidence.legal_hold_created", request)
    return hold


@transaction.atomic
def release_legal_hold(*, tenant_id, actor, hold_id, request=None):
    tenant, _, _ = _scope(tenant_id)
    actor = current_actor(actor, tenant, "authorizations:write")
    hold = ResourceLegalHold.objects.filter(tenant=tenant, public_id=hold_id).first()
    if hold is None:
        raise NotFound()
    if hold.released_at is None:
        _transition(
            hold, released_at=timezone.now(), released_by_id_snapshot=identity(actor)
        )
        _audit(hold, actor, "evidence.legal_hold_released", request)
    return hold


def restrict_subject_resources(subject, *, actor=None, request=None):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Subject restrictions require the privacy transaction.")
    from apps.evidence.models import SubjectResourceRestriction
    from apps.claims.models import Claim, ClaimDisclosure
    from apps.claims.services import invalidate_claim_tree

    lock_audit_chain(subject.tenant_id)
    now = timezone.now()
    restriction = SubjectResourceRestriction.objects.filter(
        subject=subject, tenant_id=subject.tenant_id
    ).first()
    if restriction is None:
        restriction = SubjectResourceRestriction.objects.create(
            tenant=subject.tenant,
            subject=subject,
            processing_revoked_at=now,
            reason_code="subject_deletion_requested",
            requested_by_id_snapshot=identity(actor) if actor is not None else "",
        )
        _audit(restriction, actor, "governed_resource.subject_use_restricted", request)
    for grant in PurposeAuthorization.objects.filter(
        tenant_id=subject.tenant_id, subject=subject, revoked_at__isnull=True
    ):
        _transition(
            grant, revoked_at=now, revocation_reason="subject_deletion_requested"
        )
    for item in Evidence.objects.filter(
        tenant_id=subject.tenant_id, subject=subject, status="active"
    ):
        invalidate_evidence_tree(
            item, reason="subject_deletion_requested", actor=actor, request=request
        )
    for item in Claim.objects.filter(
        tenant_id=subject.tenant_id, subject=subject, status="active"
    ):
        invalidate_claim_tree(
            item, reason="subject_deletion_requested", actor=actor, request=request
        )
    for item in ClaimDisclosure.objects.filter(
        tenant_id=subject.tenant_id, subject=subject, revoked_at__isnull=True
    ):
        _transition(item, revoked_at=now)
    from apps.providers.models import ProviderOperation

    for operation in ProviderOperation.objects.filter(
        tenant_id=subject.tenant_id,
        verification__verification_subject=subject,
        status__in=["created", "pending"],
    ):
        _transition(
            operation,
            status="cancelled",
            completed_at=now,
            invalidation_reason="subject_deletion_requested",
            remote_action="cancel",
            remote_action_status="pending",
            remote_requested_at=now,
        )
        _audit(
            operation,
            actor,
            "provider.operation_cancelled",
            request,
            reason="subject_deletion_requested",
        )
    return restriction


def scrub_subject_resources(subject, *, actor=None, request=None):
    """Called within the existing privacy transaction after hold admission."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Subject resource erasure requires its privacy transaction.")
    lock_audit_chain(subject.tenant_id)
    if active_subject_holds(subject):
        raise ValidationError("A legal hold prevents governed resource destruction.")
    from apps.claims.models import Claim, ClaimDisclosure, ClaimResolution
    from apps.claims.services import invalidate_claim_tree

    restrict_subject_resources(subject, actor=actor, request=request)
    now = timezone.now()
    counts = {"evidence": 0, "claims": 0, "authorizations": 0, "disclosures": 0}
    for grant in (
        PurposeAuthorization.objects.filter(
            tenant_id=subject.tenant_id, subject=subject
        )
        .select_related("tenant", "project")
        .iterator(chunk_size=100)
    ):
        _transition(
            grant,
            justification_json={},
            purpose="",
            revoked_at=grant.revoked_at or now,
            revocation_reason="subject_deleted",
            deleted_at=now,
        )
        counts["authorizations"] += 1
    for record in (
        Evidence.objects.filter(tenant_id=subject.tenant_id, subject=subject)
        .select_related("tenant", "project")
        .iterator(chunk_size=100)
    ):
        invalidate_evidence_tree(
            record, reason="subject_deleted", actor=actor, request=request
        )
        _transition(
            record,
            payload_json={},
            provenance_json={},
            payload_sha256="",
            provenance_sha256="",
            purpose="",
            operation_reference="",
            status="deleted",
            deleted_at=now,
            invalidated_at=now,
            invalidation_reason="subject_deleted",
        )
        counts["evidence"] += 1
    for record in (
        Claim.objects.filter(tenant_id=subject.tenant_id, subject=subject)
        .select_related("tenant", "project")
        .iterator(chunk_size=100)
    ):
        invalidate_claim_tree(
            record, reason="subject_deleted", actor=actor, request=request
        )
        _transition(
            record,
            value_json={},
            rule_parameters_json={},
            value_sha256="",
            confidence=None,
            purpose="",
            status="deleted",
            deleted_at=now,
            invalidated_at=now,
            invalidation_reason="subject_deleted",
        )
        counts["claims"] += 1
    for record in ClaimDisclosure.objects.filter(
        tenant_id=subject.tenant_id, subject=subject
    ).iterator(chunk_size=100):
        _transition(
            record,
            purpose="",
            selections_json=[],
            revoked_at=record.revoked_at or now,
            deleted_at=now,
        )
        counts["disclosures"] += 1
    for record in (
        ClaimResolution.objects.filter(tenant_id=subject.tenant_id, subject=subject)
        .select_related("tenant", "project")
        .iterator(chunk_size=100)
    ):
        _transition(record, reason_json={}, purpose="", deleted_at=now)
    for hold in (
        ResourceLegalHold.objects.filter(tenant_id=subject.tenant_id, subject=subject)
        .select_related("tenant", "project")
        .iterator(chunk_size=100)
    ):
        _transition(hold, reason_json={}, deleted_at=now)
    from apps.providers.models import ProviderOperation

    for operation in ProviderOperation.objects.filter(
        tenant_id=subject.tenant_id,
        verification__verification_subject=subject,
    ).select_related("tenant", "project"):
        _transition(
            operation,
            result_json={},
            result_sha256="",
            status="cancelled",
            completed_at=operation.completed_at or now,
            invalidation_reason="subject_deleted",
            deleted_at=now,
            remote_action="delete",
            remote_action_status="pending",
            remote_requested_at=now,
        )
        _audit(operation, actor, "provider.operation_erased", request)
    return counts


def subject_resource_export(subject):
    """Only the privileged subject-export service may call this payload builder."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Subject export requires a serialized privacy transaction.")
    from apps.claims.models import Claim

    result = {"evidence": [], "claims": []}
    for record in Evidence.objects.filter(
        tenant_id=subject.tenant_id, subject=subject, deleted_at__isnull=True
    ).select_related("tenant", "project", "schema"):
        result["evidence"].append(
            {
                "id": record.public_id,
                "project_id": record.project.public_id,
                "schema_id": record.schema.public_id,
                "purpose": record.purpose,
                "status": record.status,
                "values_redacted": True,
                "valid_until": record.valid_until.isoformat(),
                "delete_after": record.delete_after.isoformat(),
            }
        )
    for record in Claim.objects.filter(
        tenant_id=subject.tenant_id, subject=subject, deleted_at__isnull=True
    ).select_related("tenant", "project", "schema"):
        result["claims"].append(
            {
                "id": record.public_id,
                "project_id": record.project.public_id,
                "schema_id": record.schema.public_id,
                "purpose": record.purpose,
                "status": record.status,
                "claim_class": record.claim_class,
                "values_redacted": True,
                "valid_until": record.valid_until.isoformat(),
                "delete_after": record.delete_after.isoformat(),
            }
        )
    return result


@transaction.atomic
def retire_expired_resources(*, tenant_id, limit=100):
    """Bounded operator task; expired use is denied even before scrubbing runs."""
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Retention batch size must be between one and one thousand.")
    lock_audit_chain(tenant_id)
    Tenant.objects.get(pk=tenant_id)
    from apps.claims.models import Claim, ClaimDisclosure, ClaimResolution
    from apps.claims.services import invalidate_claim_tree

    now = timezone.now()
    counts = {
        "evidence": 0,
        "claims": 0,
        "authorizations": 0,
        "disclosures": 0,
        "held": 0,
    }
    from django.db import models
    from django.db.models import Exists, OuterRef

    candidates = []
    for model, category, deadline_field in (
        (Evidence, "evidence", "delete_after"),
        (Claim, "claims", "delete_after"),
        (PurposeAuthorization, "authorizations", "delete_after"),
        (ClaimDisclosure, "disclosures", "expires_at"),
        (ClaimResolution, "reviews", "delete_after"),
    ):
        scoped_holds = ResourceLegalHold.objects.filter(
            tenant_id=tenant_id,
            subject_id=OuterRef("subject_id"),
            project_id=OuterRef("project_id"),
            released_at__isnull=True,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        legacy_holds = (
            RetentionLegalHold.objects.filter(released_at__isnull=True)
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
            .filter(
                Q(tenant_id=tenant_id, verification__isnull=True)
                | Q(
                    verification__verification_subject_id=OuterRef("subject_id"),
                    verification__project_id=OuterRef("project_id"),
                )
            )
        )
        due = (
            model.objects.filter(
                tenant_id=tenant_id,
                deleted_at__isnull=True,
                **{deadline_field + "__lte": now},
            )
            .annotate(
                resource_held=Exists(scoped_holds), legacy_held=Exists(legacy_holds)
            )
            .filter(resource_held=False, legacy_held=False)
            .defer(
                *[
                    field.name
                    for field in model._meta.fields
                    if isinstance(field, models.JSONField)
                ]
            )
            .select_related("tenant", "project", "subject")
            .order_by(deadline_field, "pk")[:limit]
        )
        candidates.extend(
            (getattr(record, deadline_field), category, record.pk, record)
            for record in due
        )
    # Compare deadlines across classes; a busy evidence queue cannot starve claims.
    for _, category, _, record in sorted(candidates, key=lambda item: item[:3])[:limit]:
        if active_subject_holds(record.subject, record.project, now=now):
            counts["held"] += 1
            continue
        if category == "evidence":
            invalidate_evidence_tree(record, reason="retention_expired")
            _transition(
                record,
                payload_json={},
                provenance_json={},
                payload_sha256="",
                provenance_sha256="",
                purpose="",
                operation_reference="",
                status="deleted",
                deleted_at=now,
                invalidated_at=now,
                invalidation_reason="retention_expired",
            )
        elif category == "claims":
            invalidate_claim_tree(record, reason="retention_expired")
            _transition(
                record,
                value_json={},
                value_sha256="",
                rule_parameters_json={},
                confidence=None,
                purpose="",
                status="deleted",
                deleted_at=now,
                invalidated_at=now,
                invalidation_reason="retention_expired",
            )
        elif category == "authorizations":
            _transition(
                record,
                justification_json={},
                purpose="",
                revoked_at=record.revoked_at or now,
                revocation_reason="retention_expired",
                deleted_at=now,
            )
        elif category == "disclosures":
            _transition(
                record,
                revoked_at=record.revoked_at or now,
                selections_json=[],
                purpose="",
                deleted_at=now,
            )
        else:
            _transition(record, reason_json={}, purpose="", deleted_at=now)
        _audit(record, None, "governed_resource.retired", reason="retention_expired")
        counts[category] = counts.get(category, 0) + 1
    return counts
