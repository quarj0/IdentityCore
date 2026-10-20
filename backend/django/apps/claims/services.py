"""Reusable claims with live provenance, explicit reuse and conflict handling."""

import hmac

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.claims.models import Claim, ClaimEvidence, ClaimResolution, ClaimSource
from apps.claims.rules import apply_rule
from apps.evidence.access import (
    current_actor,
    identity,
    require_authorization,
    protected_value,
)
from apps.evidence.models import AuthorizationReuse, Evidence, ResourceSchema
from apps.evidence.services import _audit, _authorization, _scope, _transition, ancestry
from apps.evidence.validation import digest, validate_payload

MAX_CLAIM_NODES = 256
MAX_CLAIM_DEPTH = 32
MAX_SOURCES = 16


def _select_related():
    return Claim.objects.select_related(
        "tenant",
        "project",
        "subject",
        "schema",
        "authorization__tenant",
        "authorization__project",
        "authorization__subject",
        "authorization__consent_record__verification",
    )


def _reuse_allowed(target, source):
    if (target.tenant_id, target.project_id, target.subject_id) != (
        source.tenant_id,
        source.project_id,
        source.subject_id,
    ):
        raise PermissionDenied("Claim provenance is unavailable.")
    if (
        target.purpose != source.purpose
        and not AuthorizationReuse.objects.filter(
            authorization=target.authorization,
            source_authorization=source.authorization,
        ).exists()
    ):
        raise PermissionDenied("Explicit secondary-purpose approval is required.")


def _claim_value(record):
    value = protected_value(record, "value_json")
    if not hmac.compare_digest(digest(value), record.value_sha256):
        raise PermissionDenied("Claim integrity could not be verified.")
    return value


def claim_lineage(record):
    """Recheck every dependency, not just a cached derived-claim state."""
    now = timezone.now()
    claims = {}
    evidence = {}
    heights = {}
    visiting = set()

    def visit(item, depth):
        if depth > MAX_CLAIM_DEPTH or item.pk in visiting:
            raise PermissionDenied(
                "Claim lineage is invalid or exceeds its depth limit."
            )
        if item.pk in heights:
            return heights[item.pk]
        if len(claims) + len(evidence) >= MAX_CLAIM_NODES:
            raise PermissionDenied("Claim lineage exceeds its node limit.")
        if (
            item.deleted_at
            or item.status != "active"
            or not item.valid_from <= now < item.valid_until
            or now >= item.delete_after
        ):
            raise PermissionDenied("A source claim is unavailable.")
        require_authorization(item.authorization, operation="claims:read", at=now)
        _claim_value(item)
        claims[item.pk] = item
        visiting.add(item.pk)
        parent_heights = []
        for parent in (
            _select_related().filter(derived_edges__claim=item).order_by("pk")
        ):
            _reuse_allowed(item, parent)
            parent_heights.append(visit(parent, depth + 1))
        for parent in Evidence.objects.select_related(
            "authorization__tenant",
            "authorization__project",
            "authorization__subject",
            "authorization__consent_record__verification",
            "source_check__provider",
        ).filter(claim_edges__claim=item):
            _reuse_allowed(item, parent)
            for key, value in ancestry(parent).items():
                evidence[key] = value
            if len(claims) + len(evidence) > MAX_CLAIM_NODES:
                raise PermissionDenied("Claim lineage exceeds its node limit.")
            if not hmac.compare_digest(
                digest(protected_value(parent, "payload_json")), parent.payload_sha256
            ):
                raise PermissionDenied("Supporting evidence integrity failed.")
        if not item.evidence_edges.exists() and not item.source_edges.exists():
            raise PermissionDenied("A claim without provenance is unavailable.")
        visiting.remove(item.pk)
        height = 1 + max(parent_heights, default=0)
        if height > MAX_CLAIM_DEPTH:
            raise PermissionDenied("Claim lineage exceeds its depth limit.")
        heights[item.pk] = height
        return height

    visit(record, 1)
    return claims, evidence


def _independent_roots(groups):
    authorities = []
    for evidence in groups:
        roots = [item for item in evidence.values() if not item.source_edges.exists()]
        group = set()
        for item in roots:
            check = item.source_check
            if (
                check is None
                or check.status != "completed"
                or protected_value(check, "normalized_result_json").get("status") != "completed"
            ):
                raise ValidationError(
                    "Automatic corroboration requires completed, provider-bound evidence roots."
                )
            group.add(check.provider_id)
        if not group or any(group & other for other in authorities):
            raise ValidationError(
                "Corroboration sources must have independent provider authorities."
            )
        authorities.append(group)


@transaction.atomic
def create_claim(
    *,
    tenant_id,
    actor,
    project_id,
    subject_id,
    authorization_id,
    schema_id,
    observed_at,
    valid_from,
    valid_until,
    delete_after,
    evidence_ids=(),
    claim_ids=(),
    value=None,
    confidence=None,
    rule_name="",
    rule_version=1,
    rule_parameters=None,
    supersedes_id=None,
    request=None,
):
    tenant, project, subject = _scope(tenant_id, project_id, subject_id)
    actor = current_actor(actor, tenant, "claims:write", project=project)
    if evidence_ids:
        current_actor(actor, tenant, "evidence:read", project=project)
    if claim_ids:
        current_actor(actor, tenant, "claims:read", project=project)
    auth = _authorization(tenant, project, subject, authorization_id, "claims:write")
    for ids in (evidence_ids, claim_ids):
        if (
            not isinstance(ids, (list, tuple))
            or len(ids) > MAX_SOURCES
            or any(not isinstance(x, str) for x in ids)
            or len(set(ids)) != len(ids)
        ):
            raise ValidationError("Choose distinct bounded source identifiers.")
    if (
        not evidence_ids
        and not claim_ids
        or len(evidence_ids) + len(claim_ids) > MAX_SOURCES
    ):
        raise ValidationError(
            "A claim requires between one and sixteen provenance sources."
        )
    now = timezone.now()
    if (
        any(
            timezone.is_naive(t)
            for t in (observed_at, valid_from, valid_until, delete_after)
        )
        or observed_at > now
        or valid_from > now
        or valid_until <= now
        or valid_until <= valid_from
        or delete_after < valid_until
        or valid_until > auth.valid_until
    ):
        raise ValidationError(
            "Claim validity must fit current authorization and retention."
        )
    schema = ResourceSchema.objects.filter(
        tenant=tenant, public_id=schema_id, kind="claim", retired_at__isnull=True
    ).first()
    if schema is None:
        raise NotFound()
    evidence = list(
        Evidence.objects.select_related(
            "authorization__tenant",
            "authorization__project",
            "authorization__subject",
            "authorization__consent_record__verification",
            "source_check__provider",
        ).filter(
            tenant=tenant, project=project, subject=subject, public_id__in=evidence_ids
        )
    )
    claims = list(
        _select_related().filter(
            tenant=tenant, project=project, subject=subject, public_id__in=claim_ids
        )
    )
    if len(evidence) != len(evidence_ids) or len(claims) != len(claim_ids):
        raise NotFound()
    source_map = {item.public_id: item for item in [*evidence, *claims]}
    # Stable input order is part of the versioned rule contract, not SQL order.
    ordered = [source_map[key] for key in [*evidence_ids, *claim_ids]]
    values, groups = [], []
    for source in ordered:
        if (
            source.purpose != auth.purpose
            and not AuthorizationReuse.objects.filter(
                authorization=auth, source_authorization=source.authorization
            ).exists()
        ):
            raise PermissionDenied("Explicit secondary-purpose approval is required.")
        if isinstance(source, Claim):
            _, roots = require_usable_claim(source)
            groups.append(roots)
            values.append(_claim_value(source))
        else:
            groups.append(ancestry(source))
            if digest(protected_value(source, "payload_json")) != source.payload_sha256:
                raise PermissionDenied("Supporting evidence integrity failed.")
            values.append(protected_value(source, "payload_json"))
        if valid_until > source.valid_until or delete_after > source.delete_after:
            raise ValidationError("A claim cannot outlive its supporting sources.")
    if rule_parameters is not None and not isinstance(rule_parameters, dict):
        raise ValidationError("Rule parameters must be an object.")
    parameters = rule_parameters if rule_parameters is not None else {}
    claim_class = "candidate"
    if rule_name:
        if value is not None or confidence is not None:
            raise ValidationError(
                "Rule-derived values and confidence cannot be supplied by the caller."
            )
        value, claim_class, deadline = apply_rule(
            rule_name, rule_version, values, parameters, now=now
        )
        if deadline is not None and valid_until > deadline:
            raise ValidationError(
                "Time-dependent predicates must expire by the next UTC date."
            )
        if rule_name == "exact_corroboration":
            _independent_roots(groups)
        source_confidences = [item.confidence for item in claims]
        confidence = (
            min(source_confidences)
            if source_confidences and all(c is not None for c in source_confidences)
            else None
        )
    elif parameters or rule_version != 1:
        raise ValidationError("Rule parameters require a supported rule.")
    payload_hash = validate_payload(schema, value)
    old = None
    if supersedes_id:
        old = (
            _select_related()
            .filter(
                tenant=tenant,
                project=project,
                subject=subject,
                purpose=auth.purpose,
                schema=schema,
                public_id=supersedes_id,
                status="active",
            )
            .first()
        )
        if old is None:
            raise NotFound()
        ancestor_claim_ids = {
            key for source in claims for key in claim_lineage(source)[0]
        }
        if old.pk in ancestor_claim_ids:
            raise ValidationError("A correction cannot depend on its predecessor.")
    record = Claim.objects.create(
        tenant=tenant,
        project=project,
        subject=subject,
        authorization=auth,
        schema=schema,
        purpose=auth.purpose,
        claim_class=claim_class,
        value_json=value,
        value_sha256=payload_hash,
        confidence=confidence,
        rule_name=rule_name,
        rule_version=rule_version,
        rule_parameters_json=parameters,
        observed_at=observed_at,
        valid_from=valid_from,
        valid_until=valid_until,
        delete_after=delete_after,
        supersedes=old,
        created_by_id_snapshot=identity(actor),
    )
    for item in evidence:
        ClaimEvidence.objects.create(claim=record, evidence=item)
    for item in claims:
        ClaimSource.objects.create(claim=record, source=item)
    # Creation may have a write-only authorization. Validate its dependencies,
    # then enforce aggregate graph bounds without silently widening read grants.
    existing_claims, existing_evidence = set(), set()
    for item in claims:
        cs, es = claim_lineage(item)
        existing_claims.update(cs)
        existing_evidence.update(es)
    for group in groups:
        existing_evidence.update(group)
    all_ids = existing_claims | {record.pk}
    parents = {key: [] for key in all_ids}
    for child_id, parent_id in ClaimSource.objects.filter(
        claim_id__in=all_ids
    ).values_list("claim_id", "source_id"):
        if parent_id not in all_ids:
            raise PermissionDenied("Claim ancestry could not be established.")
        parents[child_id].append(parent_id)
    heights = {}
    for key in sorted(all_ids):
        heights[key] = 1 + max((heights[parent] for parent in parents[key]), default=0)
    if heights[record.pk] > MAX_CLAIM_DEPTH:
        raise ValidationError("Claim lineage exceeds the depth limit.")
    if len(existing_claims) + len(existing_evidence) + 1 > MAX_CLAIM_NODES:
        raise ValidationError("Claim lineage exceeds the node limit.")
    if old is not None:
        invalidate_claim_tree(
            old, reason="superseded", status="superseded", actor=actor, request=request
        )
    _audit(
        record,
        actor,
        "claims.created",
        request,
        claim_class=claim_class,
        schema_id=schema.public_id,
        source_count=len(ordered),
    )
    return record


def invalidate_claim_tree(
    record, *, reason, status="revoked", actor=None, request=None
):
    now = timezone.now()
    frontier, seen = {record.pk}, set()
    while frontier:
        batch = sorted(frontier - seen)
        if not batch:
            break
        seen.update(batch)
        for item in Claim.objects.filter(tenant_id=record.tenant_id, pk__in=batch):
            if item.status == "active":
                _transition(
                    item,
                    status=status if item.pk == record.pk else "revoked",
                    invalidated_at=now,
                    invalidation_reason=reason,
                )
                _audit(item, actor, "claims.invalidated", request, reason=reason)
        frontier = (
            set(
                ClaimSource.objects.filter(
                    source_id__in=batch, claim__tenant_id=record.tenant_id
                ).values_list("claim_id", flat=True)
            )
            - seen
        )
    return seen


def current_conflict(record):
    """No confidence ranking: a decision must bind the entire current member set."""
    now = timezone.now()
    candidates = _select_related().filter(
        tenant_id=record.tenant_id,
        project_id=record.project_id,
        subject_id=record.subject_id,
        purpose=record.purpose,
        schema_id=record.schema_id,
        status="active",
        deleted_at__isnull=True,
        valid_from__lte=now,
        valid_until__gt=now,
        delete_after__gt=now,
    )
    if candidates.count() > MAX_CLAIM_NODES:
        raise ValidationError("Conflict set exceeds its supported bound.")
    members = []
    for candidate in candidates.order_by("pk"):
        try:
            claim_lineage(candidate)
        except PermissionDenied:
            continue
        members.append(candidate)
    if len(members) > MAX_CLAIM_NODES:
        raise ValidationError("Conflict set exceeds its supported bound.")
    values = {digest(_claim_value(item)) for item in members}
    ids = sorted(item.public_id for item in members)
    resolution = (
        ClaimResolution.objects.filter(
            tenant_id=record.tenant_id,
            project_id=record.project_id,
            subject_id=record.subject_id,
            schema_id=record.schema_id,
            purpose=record.purpose,
        )
        .order_by("-created_at", "-pk")
        .first()
    )
    if resolution is not None and resolution.member_ids_json == ids:
        return members, resolution
    return members, None if len(values) <= 1 else False


@transaction.atomic
def resolve_conflict(
    *,
    tenant_id,
    actor,
    project_id,
    claim_id,
    purpose,
    selected_claim_id,
    outcome,
    reason,
    request=None,
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:write", project=project)
    # Resolution is a human review, not a machine credential's state override.
    from apps.accounts.models import PlatformUser
    from common.authorization import AuthorizationAction, decide_user_access

    if (
        not isinstance(actor, PlatformUser)
        or not decide_user_access(
            actor,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=tenant,
            permission_code="review_verification",
        ).allowed
    ):
        raise PermissionDenied("Independent reviewer authority is required.")
    record = (
        _select_related()
        .filter(tenant=tenant, project=project, purpose=purpose, public_id=claim_id)
        .first()
    )
    if record is None:
        raise NotFound()
    claim_lineage(record)
    members, _ = current_conflict(record)
    if not members:
        raise ValidationError("The claim does not have an available review set.")
    if any(item.created_by_id_snapshot == identity(actor) for item in members):
        raise PermissionDenied("A claim maker cannot resolve its conflict.")
    selected = next(
        (item for item in members if item.public_id == selected_claim_id), None
    )
    if (
        outcome not in {"selected", "disputed", "more_evidence"}
        or (outcome == "selected") != (selected is not None)
        or (outcome != "selected" and selected_claim_id is not None)
    ):
        raise ValidationError("Choose an outcome and a matching current member.")
    from apps.evidence.validation import canonical_json

    canonical_json(reason, maximum=32 * 1024)
    if not isinstance(reason, dict) or not reason:
        raise ValidationError("Document the conflict resolution reason.")
    result = ClaimResolution.objects.create(
        tenant=tenant,
        project=project,
        subject=record.subject,
        schema=record.schema,
        purpose=purpose,
        selected_claim=selected,
        member_ids_json=sorted(item.public_id for item in members),
        delete_after=min(item.delete_after for item in members),
        outcome=outcome,
        reason_json=reason,
        decided_by_id_snapshot=identity(actor),
    )
    _audit(
        result,
        actor,
        "claims.conflict_resolved",
        request,
        outcome=outcome,
        member_count=len(members),
    )
    return result


@transaction.atomic
def read_claim(
    *,
    tenant_id,
    actor,
    project_id,
    claim_id,
    purpose,
    include_value=False,
    request=None,
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:read", project=project)
    record = (
        _select_related()
        .filter(tenant=tenant, project=project, purpose=purpose, public_id=claim_id)
        .first()
    )
    if record is None:
        raise NotFound()
    graph, _ = claim_lineage(record)
    inherited_conflict = False
    for source in graph.values():
        if source.pk != record.pk:
            _, decision = current_conflict(source)
            if (
                decision is False
                or decision is not None
                and (
                    decision.outcome != "selected"
                    or decision.selected_claim_id != source.pk
                )
            ):
                inherited_conflict = True
    _, resolution = current_conflict(record)
    state = (
        "disputed"
        if inherited_conflict
        or resolution is False
        or (
            resolution is not None
            and (
                resolution.outcome != "selected"
                or resolution.selected_claim_id != record.pk
            )
        )
        else "active"
    )
    payload = {
        "id": record.public_id,
        "project_id": project.public_id,
        "subject_id": record.subject.public_id,
        "schema_id": record.schema.public_id,
        "schema_version": record.schema.version,
        "purpose": purpose,
        "claim_class": "reviewed"
        if resolution
        and resolution.outcome == "selected"
        and resolution.selected_claim_id == record.pk
        else record.claim_class,
        "status": state,
        "confidence": str(record.confidence) if record.confidence is not None else None,
        "observed_at": record.observed_at.isoformat(),
        "valid_from": record.valid_from.isoformat(),
        "valid_until": record.valid_until.isoformat(),
        "delete_after": record.delete_after.isoformat(),
        "rule": {"name": record.rule_name, "version": record.rule_version}
        if record.rule_name
        else None,
        "source_evidence_ids": list(
            record.source_evidence.values_list("public_id", flat=True)
        ),
        "source_claim_ids": list(
            record.source_claims.values_list("public_id", flat=True)
        ),
    }
    if include_value:
        payload["value"] = _claim_value(record)
    _audit(record, actor, "claims.accessed", request, value_included=include_value)
    return payload


def require_usable_claim(record):
    graph, evidence = claim_lineage(record)
    for source in graph.values():
        _, decision = current_conflict(source)
        if (
            decision is False
            or decision is not None
            and (
                decision.outcome != "selected"
                or decision.selected_claim_id != source.pk
            )
        ):
            raise PermissionDenied(
                "An unresolved or rejected claim conflict prevents reuse."
            )
    return graph, evidence


@transaction.atomic
def revoke_claim(
    *, tenant_id, actor, project_id, claim_id, purpose, reason, request=None
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:write", project=project)
    record = (
        _select_related()
        .filter(tenant=tenant, project=project, public_id=claim_id, purpose=purpose)
        .first()
    )
    if record is None:
        raise NotFound()
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 120:
        raise ValidationError("A bounded revocation reason code is required.")
    invalidate_claim_tree(record, reason=reason, actor=actor, request=request)
    return record
