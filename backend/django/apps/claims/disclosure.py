"""Live policy evaluation and audience-bound disclosure without persisted values."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.api_clients.models import APIClient
from apps.claims.models import (
    ClaimDisclosure,
    ClaimDisclosureRedemption,
    ClaimReusePolicy,
)
from apps.claims.services import (
    _claim_value,
    _select_related,
    current_conflict,
    require_usable_claim,
)
from apps.evidence.access import current_actor, identity, require_authorization
from apps.evidence.models import PurposeAuthorization, ResourceSchema
from apps.evidence.services import _audit, _scope, _transition

CLAIM_CLASSES = {
    "candidate",
    "provider_asserted",
    "normalized",
    "corroborated",
    "derived",
    "reviewed",
}
MAX_DISCLOSURE_SECONDS = 900


@transaction.atomic
def propose_policy(
    *,
    tenant_id,
    actor,
    project_id,
    schema_id,
    name,
    version,
    purposes,
    accepted_classes,
    fields,
    max_age_seconds,
    minimum_confidence=None,
    request=None,
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:write", project=project)
    schema = ResourceSchema.objects.filter(
        tenant=tenant, public_id=schema_id, kind="claim", retired_at__isnull=True
    ).first()
    if schema is None:
        raise NotFound()
    for values in (purposes, accepted_classes, fields):
        if (
            not isinstance(values, list)
            or not values
            or len(values) > 32
            or any(
                not isinstance(value, str) or not value or len(value) > 255
                for value in values
            )
            or len(values) != len(set(values))
        ):
            raise ValidationError("Policy lists must contain distinct bounded values.")
    if not set(accepted_classes).issubset(CLAIM_CLASSES) or not set(fields).issubset(
        schema.disclosure_fields_json
    ):
        raise ValidationError(
            "Policy classes and fields must be explicitly permitted by the schema."
        )
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 366 * 86400:
        raise ValidationError(
            "Choose a freshness interval between one second and 366 days."
        )
    policy = ClaimReusePolicy.objects.create(
        tenant=tenant,
        project=project,
        schema=schema,
        name=name,
        version=version,
        purposes_json=purposes,
        accepted_classes_json=accepted_classes,
        disclosure_fields_json=fields,
        max_age_seconds=max_age_seconds,
        minimum_confidence=minimum_confidence,
        proposed_by_id_snapshot=identity(actor),
    )
    _audit(policy, actor, "claims.reuse_policy_proposed", request)
    return policy


@transaction.atomic
def approve_policy(*, tenant_id, actor, project_id, policy_id, request=None):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "authorizations:approve", project=project)
    current_actor(actor, tenant, "claims:read", project=project)
    policy = ClaimReusePolicy.objects.filter(
        tenant=tenant, project=project, public_id=policy_id, retired_at__isnull=True
    ).first()
    if policy is None:
        raise NotFound()
    if policy.proposed_by_id_snapshot == identity(actor):
        raise PermissionDenied("A different privacy officer must approve the policy.")
    if policy.approved_at is None:
        _transition(
            policy, approved_at=timezone.now(), approved_by_id_snapshot=identity(actor)
        )
        _audit(policy, actor, "claims.reuse_policy_approved", request)
    return policy


def evaluate(record, policy, *, now=None):
    now = now or timezone.now()
    if (
        (policy.tenant_id, policy.project_id, policy.schema_id)
        != (record.tenant_id, record.project_id, record.schema_id)
        or record.purpose not in policy.purposes_json
        or not policy.approved_at
        or policy.retired_at
    ):
        raise PermissionDenied(
            "An approved policy matching the claim context is required."
        )
    claims, evidence = require_usable_claim(record)
    _, resolution = current_conflict(record)
    effective_class = (
        "reviewed"
        if resolution
        and resolution.outcome == "selected"
        and resolution.selected_claim_id == record.pk
        else record.claim_class
    )
    oldest = min(item.observed_at for item in [*claims.values(), *evidence.values()])
    fresh_until = oldest + timedelta(seconds=policy.max_age_seconds)
    reasons = []
    if effective_class not in policy.accepted_classes_json:
        reasons.append("claim_class_not_accepted")
    if now >= fresh_until:
        reasons.append("source_not_fresh")
    if policy.minimum_confidence is not None and (
        record.confidence is None or record.confidence < policy.minimum_confidence
    ):
        reasons.append("confidence_requirement_not_met")
    deadline = min(
        [
            fresh_until,
            *[
                min(item.valid_until, item.delete_after, item.authorization.valid_until)
                for item in [*claims.values(), *evidence.values()]
            ],
        ]
    )
    return {
        "satisfied": not reasons,
        "reason_codes": reasons,
        "claim_class": effective_class,
        "fresh_until": fresh_until.isoformat(),
        "usable_until": deadline.isoformat(),
    }, deadline


@transaction.atomic
def evaluate_claim(
    *, tenant_id, actor, project_id, claim_id, purpose, policy_id, request=None
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:read", project=project)
    record = (
        _select_related()
        .filter(tenant=tenant, project=project, purpose=purpose, public_id=claim_id)
        .first()
    )
    policy = ClaimReusePolicy.objects.filter(
        tenant=tenant, project=project, public_id=policy_id
    ).first()
    if record is None or policy is None:
        raise NotFound()
    result, _ = evaluate(record, policy)
    _audit(
        record,
        actor,
        "claims.policy_evaluated",
        request,
        policy_id=policy.public_id,
        satisfied=result["satisfied"],
    )
    return {"claim_id": record.public_id, "policy_id": policy.public_id, **result}


def _selections(*, tenant, project, authorization, selections):
    if not isinstance(selections, list) or not 1 <= len(selections) <= 16:
        raise ValidationError("Select between one and sixteen claims.")
    output, stable, deadlines, seen = [], [], [], set()
    for selection in selections:
        if not isinstance(selection, dict) or set(selection) != {
            "claim_id",
            "policy_id",
            "fields",
        }:
            raise ValidationError(
                "Each selection needs claim_id, policy_id and fields."
            )
        claim_id, policy_id, fields = (
            selection["claim_id"],
            selection["policy_id"],
            selection["fields"],
        )
        if (
            not isinstance(claim_id, str)
            or not isinstance(policy_id, str)
            or len(claim_id) > 64
            or len(policy_id) > 64
            or claim_id in seen
        ):
            raise ValidationError("Select distinct bounded claim identifiers.")
        seen.add(claim_id)
        record = (
            _select_related()
            .filter(
                tenant=tenant,
                project=project,
                subject=authorization.subject,
                purpose=authorization.purpose,
                public_id=claim_id,
            )
            .first()
        )
        policy = ClaimReusePolicy.objects.filter(
            tenant=tenant, project=project, public_id=policy_id
        ).first()
        if record is None or policy is None:
            raise NotFound()
        if (
            not isinstance(fields, list)
            or not fields
            or len(fields) > 32
            or any(not isinstance(field, str) for field in fields)
            or len(fields) != len(set(fields))
            or not set(fields).issubset(policy.disclosure_fields_json)
            or not set(fields).issubset(record.schema.disclosure_fields_json)
        ):
            raise PermissionDenied(
                "The requested fields are not permitted for disclosure."
            )
        result, deadline = evaluate(record, policy)
        if not result["satisfied"]:
            raise PermissionDenied(
                "The selected claim does not satisfy its reuse policy."
            )
        value = _claim_value(record)
        if any(field not in value for field in fields):
            raise PermissionDenied("A requested disclosure field is unavailable.")
        output.append(
            {
                "claim_id": record.public_id,
                "schema_id": record.schema.public_id,
                "schema_version": record.schema.version,
                "policy_id": policy.public_id,
                "claim_class": result["claim_class"],
                "observed_at": record.observed_at.isoformat(),
                "value": {field: value[field] for field in fields},
            }
        )
        stable.append(
            {
                "claim_id": record.public_id,
                "policy_id": policy.public_id,
                "fields": fields,
            }
        )
        deadlines.append(deadline)
    return output, stable, min(deadlines)


@transaction.atomic
def issue_disclosure(
    *,
    tenant_id,
    actor,
    project_id,
    authorization_id,
    audience_id,
    selections,
    lifetime_seconds=300,
    max_redemptions=1,
    request=None,
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:disclose", project=project)
    authorization = (
        PurposeAuthorization.objects.select_related(
            "tenant", "project", "subject", "consent_record__verification"
        )
        .filter(tenant=tenant, project=project, public_id=authorization_id)
        .first()
    )
    if authorization is None:
        raise NotFound()
    require_authorization(authorization, operation="claims:disclose")
    audience = APIClient.objects.filter(
        tenant=tenant,
        project=project,
        public_id=audience_id,
        status="active",
        deleted_at__isnull=True,
    ).first()
    if audience is None:
        raise NotFound()
    current_actor(audience, tenant, "claims:read", project=project)
    if (
        type(lifetime_seconds) is not int
        or not 1 <= lifetime_seconds <= MAX_DISCLOSURE_SECONDS
        or type(max_redemptions) is not int
        or not 1 <= max_redemptions <= 10
    ):
        raise ValidationError(
            "Choose a lifetime of 1–900 seconds and 1–10 redemptions."
        )
    _, stable, deadline = _selections(
        tenant=tenant,
        project=project,
        authorization=authorization,
        selections=selections,
    )
    now = timezone.now()
    expires_at = min(
        now + timedelta(seconds=lifetime_seconds), authorization.valid_until, deadline
    )
    if expires_at <= now:
        raise PermissionDenied("The disclosure evidence is no longer fresh.")
    raw = "icd_" + secrets.token_urlsafe(32)
    record = ClaimDisclosure.objects.create(
        tenant=tenant,
        project=project,
        subject=authorization.subject,
        authorization=authorization,
        purpose=authorization.purpose,
        audience=audience,
        selections_json=stable,
        token_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=expires_at,
        created_by_id_snapshot=identity(actor),
        max_redemptions=max_redemptions,
    )
    _audit(
        record,
        actor,
        "claims.disclosure_issued",
        request,
        audience_id=audience.public_id,
        claim_count=len(stable),
    )
    # The raw capability must never be persisted, including in idempotency data.
    return record, raw


@transaction.atomic
def redeem_disclosure(
    *, tenant_id, actor, project_id, disclosure_id, token, request_key, request=None
):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:read", project=project)
    if not isinstance(actor, APIClient):
        raise PermissionDenied("The authenticated audience credential is required.")
    if (
        not isinstance(token, str)
        or not 32 <= len(token) <= 128
        or not token.startswith("icd_")
    ):
        raise NotFound()
    record = (
        ClaimDisclosure.objects.select_related(
            "authorization__tenant",
            "authorization__project",
            "authorization__subject",
            "authorization__consent_record__verification",
        )
        .filter(tenant=tenant, project=project, audience=actor, public_id=disclosure_id)
        .first()
    )
    if record is None or not hmac.compare_digest(
        record.token_sha256, hashlib.sha256(token.encode()).hexdigest()
    ):
        raise NotFound()
    if record.deleted_at or record.revoked_at or timezone.now() >= record.expires_at:
        raise PermissionDenied("The disclosure capability is unavailable.")
    require_authorization(record.authorization, operation="claims:disclose")
    if (
        not isinstance(request_key, str)
        or not request_key.strip()
        or len(request_key) > 255
    ):
        raise ValidationError("A bounded Idempotency-Key is required for redemption.")
    fingerprint = hashlib.sha256(request_key.encode()).hexdigest()
    previous = record.redemptions.filter(
        request_key_sha256=fingerprint, audience_id_snapshot=identity(actor)
    ).exists()
    if not previous and record.redemption_count >= record.max_redemptions:
        raise PermissionDenied("The disclosure redemption limit is exhausted.")
    # Every replay reevaluates current proofs/conflicts/freshness. No cached
    # value or token survives a later withdrawal or revocation.
    output, _, _ = _selections(
        tenant=tenant,
        project=project,
        authorization=record.authorization,
        selections=record.selections_json,
    )
    if not previous:
        ClaimDisclosureRedemption.objects.create(
            tenant=tenant,
            disclosure=record,
            request_key_sha256=fingerprint,
            audience_id_snapshot=identity(actor),
        )
        _transition(record, redemption_count=record.redemption_count + 1)
    _audit(
        record,
        actor,
        "claims.disclosure_redeemed",
        request,
        replay=previous,
        claim_count=len(output),
    )
    return {
        "id": record.public_id,
        "purpose": record.purpose,
        "audience_id": actor.public_id,
        "expires_at": record.expires_at.isoformat(),
        "claims": output,
    }


@transaction.atomic
def revoke_disclosure(*, tenant_id, actor, project_id, disclosure_id, request=None):
    tenant, project, _ = _scope(tenant_id, project_id)
    actor = current_actor(actor, tenant, "claims:disclose", project=project)
    record = ClaimDisclosure.objects.filter(
        tenant=tenant, project=project, public_id=disclosure_id
    ).first()
    if record is None:
        raise NotFound()
    if record.revoked_at is None:
        _transition(record, revoked_at=timezone.now())
        _audit(record, actor, "claims.disclosure_revoked", request)
    return record


@transaction.atomic
def retire_policy(*, tenant_id, actor, project_id, policy_id, request=None):
    tenant, project, _ = _scope(tenant_id, project_id, allow_inactive_project=True)
    actor = current_actor(actor, tenant, "authorizations:write", project=project)
    policy = ClaimReusePolicy.objects.filter(
        tenant=tenant, project=project, public_id=policy_id
    ).first()
    if policy is None:
        raise NotFound()
    if policy.retired_at is None:
        _transition(policy, retired_at=timezone.now())
        _audit(policy, actor, "claims.reuse_policy_retired", request)
    return policy
