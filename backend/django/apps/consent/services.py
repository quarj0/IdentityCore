"""Purpose-bound immutable consent and an audited one-way withdrawal."""

from hashlib import sha256
from datetime import timezone as datetime_timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.consent.models import ConsentRecord
from apps.verifications.models import (
    Verification,
    ProcessingJob,
    ProcessingJobStatus,
    VerificationSessionStatus,
    VerificationReviewOwner,
)
from common.fields import environment_for_instance

ERROR = "Active consent for this purpose and evidence scope is required."
SCOPES = {"document", "biometrics"}


def evidence_scope(verification, template=None):
    snapshot = (verification.policy_snapshot_json or {}).get("consent") or {}
    value = snapshot.get("evidence_scope")
    if value is None and template is not None:
        value = template.evidence_scope_json
    if value is None:
        value = ["document", "biometrics"]
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or item not in SCOPES for item in value)
        or len(value) != len(set(value))
    ):
        raise ValidationError("Consent evidence scope is invalid.")
    return sorted(value)


def build_proof(
    record, *, notice_version=None, source="acceptance", evidence_scope_override=None
):
    case = record.verification
    if (
        record.tenant_id != case.tenant_id
        or record.verification_subject_id != case.verification_subject_id
        or (
            record.consent_template_id
            and record.consent_template.tenant_id != case.tenant_id
        )
    ):
        raise ValidationError("Consent ownership is invalid.")
    snapshot = (case.policy_snapshot_json or {}).get("consent") or {}
    frozen = (snapshot.get("translations") or {}).get(record.consent_locale) or snapshot
    version = (
        notice_version
        or frozen.get("version")
        or (record.consent_template.version if record.consent_template_id else 1)
    )
    if type(version) is not int or version < 1:
        raise ValidationError("Consent notice version is invalid.")
    scopes = (
        evidence_scope_override
        if evidence_scope_override is not None
        else frozen.get("evidence_scope")
    )
    if scopes is None:
        scopes = evidence_scope(case, record.consent_template)
    if (
        not isinstance(scopes, list)
        or any(not isinstance(item, str) or item not in SCOPES for item in scopes)
        or len(scopes) != len(set(scopes))
    ):
        raise ValidationError("Consent evidence scope is invalid.")
    return {
        "schema_version": 1,
        "record_id": record.public_id,
        "verification_id": case.public_id,
        "subject_id": case.verification_subject.public_id,
        "tenant_id": case.tenant.public_id,
        "purpose": case.purpose,
        "environment": environment_for_instance(case),
        "template_id": getattr(record, "_notice_template_id", None)
        or frozen.get("template_id")
        or (
            record.consent_template.public_id
            if record.consent_template_id
            else "generated"
        ),
        "notice_version": version,
        "locale": record.consent_locale,
        "accepted_at": record.accepted_at.astimezone(datetime_timezone.utc).isoformat(),
        "accepted": bool(record.accepted),
        "content_hash": sha256(record.consent_text_snapshot.encode()).hexdigest(),
        "evidence_scope": sorted(scopes),
        "binding_source": source,
    }


def active_consent(verification, scope=None):
    case = Verification.objects.select_related(
        "tenant", "project", "verification_subject"
    ).get(pk=verification.pk)
    onboarding_pending = (
        case.tenant.status in {"pending", "pending_review"}
        and case.review_owner == VerificationReviewOwner.PLATFORM
        and (case.metadata_json or {}).get("workflow") == "administrator_onboarding"
    )
    if (
        case.deleted_at
        or case.verification_subject.deleted_at
        or case.tenant.deleted_at
        or (case.tenant.status != "active" and not onboarding_pending)
    ):
        return None
    record = (
        ConsentRecord.objects.filter(
            verification=case,
            tenant_id=case.tenant_id,
            verification_subject_id=case.verification_subject_id,
            deleted_at__isnull=True,
        )
        .select_related("verification", "tenant")
        .order_by("-accepted_at", "-pk")
        .first()
    )
    if record is None or not record.accepted or record.withdrawn_at:
        return None
    try:
        proof = record.proof_json
        if not isinstance(proof, dict) or proof.get("schema_version") != 1:
            return None
        expected = {
            "record_id": record.public_id,
            "verification_id": case.public_id,
            "subject_id": case.verification_subject.public_id,
            "tenant_id": case.tenant.public_id,
            "purpose": case.purpose,
            "environment": environment_for_instance(case),
            "locale": record.consent_locale,
            "content_hash": sha256(record.consent_text_snapshot.encode()).hexdigest(),
            "accepted_at": record.accepted_at.astimezone(
                datetime_timezone.utc
            ).isoformat(),
            "accepted": True,
        }
        if (
            any(proof.get(key) != value for key, value in expected.items())
            or record.consent_content_hash != expected["content_hash"]
        ):
            return None
        scopes = proof.get("evidence_scope")
        if (
            not isinstance(scopes, list)
            or any(item not in SCOPES for item in scopes)
            or (scope is not None and scope not in scopes)
        ):
            return None
        frozen = (case.policy_snapshot_json or {}).get("consent") or {}
        frozen = (frozen.get("translations") or {}).get(record.consent_locale) or frozen
        if frozen.get("version") and proof.get("notice_version") != frozen["version"]:
            return None
        if type(proof.get("notice_version")) is not int or proof["notice_version"] < 1:
            return None
        return record
    except (ValueError, TypeError):
        return None


def require_active_consent(verification, scope=None):
    record = active_consent(verification, scope)
    if record is None:
        raise ValidationError(ERROR)
    return record


@transaction.atomic
def withdraw(record, *, actor=None, request=None):
    lock_audit_chain(record.tenant_id)
    case = Verification.objects.select_for_update(no_key=True).get(
        pk=record.verification_id, tenant_id=record.tenant_id
    )
    record = ConsentRecord.objects.select_for_update(no_key=True).get(
        pk=record.pk,
        tenant_id=case.tenant_id,
        verification_subject_id=case.verification_subject_id,
    )
    if not record.accepted:
        raise ValidationError(ERROR)
    if (
        record.withdrawn_at is not None
        and not ConsentRecord.objects.filter(
            verification=case, accepted=True, withdrawn_at__isnull=True
        ).exists()
    ):
        return record
    now = timezone.now()
    # Every proof in this verification is withdrawn, so an older accepted record
    # cannot restore authorization when the newest record is withdrawn.
    for proof in ConsentRecord.objects.filter(
        verification=case, accepted=True, withdrawn_at__isnull=True
    ):
        proof.withdrawn_at = now
        proof._withdrawal_authorized = True
        proof.save(update_fields=["withdrawn_at", "updated_at"])
    case.sessions.update(status=VerificationSessionStatus.REVOKED)
    ProcessingJob.objects.filter(
        verification=case,
        status__in=[ProcessingJobStatus.QUEUED, ProcessingJobStatus.PROCESSING],
    ).update(
        status=ProcessingJobStatus.EXHAUSTED,
        error_code="consent_withdrawn",
        completed_at=now,
        heartbeat_at=now,
        lease_expires_at=now,
    )
    from apps.verifications.transitions import (
        TERMINAL_STATUSES,
        transition_verification,
    )

    if case.status not in TERMINAL_STATUSES:
        from apps.verifications.models import VerificationStatus

        transition_verification(case, VerificationStatus.CANCELLED)
        from apps.webhooks.services import queue_webhook_events

        queue_webhook_events(
            tenant=case.tenant,
            event_type="verification.cancelled",
            payload={
                "verification_id": case.public_id,
                "external_reference": case.external_reference,
                "status": case.status,
            },
        )
    record_audit_event(
        tenant=case.tenant,
        actor=actor,
        request=request,
        action="consent.withdrawn",
        target_type="consent_record",
        target_id=record.public_id,
        metadata={
            "verification_id": case.public_id,
            "environment": environment_for_instance(case),
        },
    )
    record.refresh_from_db(fields=["withdrawn_at", "updated_at"])
    return record


def scope_for_check(check_type):
    if check_type in {
        "document_ocr",
        "document_quality",
        "document_classification",
        "document_authenticity",
    }:
        return "document"
    if check_type in {"face_match", "liveness"}:
        return "biometrics"
    return None
