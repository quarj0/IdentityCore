"""Durable deterministic samples, independent reviewers and private QA results."""

from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import NotFound, ValidationError

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verifications.models import (
    ReviewQueueEntry,
    ReviewQueueMember,
    ReviewQualityAssignment,
    Verification,
)
from apps.verifications.review_queues import eligible
from apps.verifications.review_reasons import CODE, validate_reviewer_input


def visible_samples(user):
    return ReviewQualityAssignment.objects.filter(
        tenant_id=user.tenant_id, deleted_at__isnull=True
    ).exclude(Q(maker=user) | Q(checker=user))


def quality_eligible(member, sample):
    return member.user_id not in {sample.maker_id, sample.checker_id} and eligible(
        member, sample.verification, sample.required_skills
    )


def allocate_locked(sample):
    if (
        sample.reviewer_id
        or sample.completed_at
        or not sample.queue.active
        or sample.queue.deleted_at is not None
    ):
        return sample
    members = list(
        sample.queue.members.select_for_update(of=("self",), no_key=True)
        .filter(available=True, deleted_at__isnull=True)
        .select_related("user")
    )
    candidates = [member for member in members if quality_eligible(member, sample)]
    if not candidates:
        return sample

    def rank(member):
        load = ReviewQualityAssignment.objects.filter(
            tenant_id=sample.tenant_id,
            queue__environment=sample.queue.environment,
            reviewer_id=member.user_id,
            completed_at__isnull=True,
            deleted_at__isnull=True,
        ).count()
        last_assignment = ReviewQueueMember.objects.filter(
            queue__tenant_id=sample.tenant_id,
            queue__environment=sample.queue.environment,
            user_id=member.user_id,
        ).aggregate(last=Max("last_assigned_at"))["last"]
        return (
            load,
            last_assignment
            or timezone.datetime.min.replace(tzinfo=timezone.get_current_timezone()),
            member.user_id,
        )

    chosen = min(candidates, key=rank)
    sample.reviewer = chosen.user
    sample.save(update_fields=["reviewer", "updated_at"])
    now = timezone.now()
    ReviewQueueMember.objects.filter(
        queue__tenant_id=sample.tenant_id,
        queue__environment=sample.queue.environment,
        user_id=chosen.user_id,
    ).update(last_assigned_at=now, updated_at=now)
    record_audit_event(
        tenant=sample.tenant,
        action="review_quality.assigned",
        target_type="review_quality",
        target_id=sample.public_id,
        metadata={"reviewer_id": chosen.user.public_id},
    )
    return sample


def sample_final_decision(verification, decision):
    """Called inside the final manual decision's tenant-locked transaction."""
    if (
        decision.decision_type != "manual"
        or decision.approval_status == "pending"
        or decision.decided_by_id is None
        or verification.status not in {"verified", "rejected", "failed"}
    ):
        return None
    entry = (
        ReviewQueueEntry.objects.filter(verification=verification)
        .select_related("queue")
        .first()
    )
    if entry is None or not entry.queue.active or entry.queue.deleted_at is not None:
        return None
    percent = entry.queue.sampling_percent or 0
    if not 0 <= percent <= 100:
        raise ValidationError("Invalid review sampling configuration.")
    digest = salted_hmac(
        "identitycore.review-quality.sample.v1",
        f"{verification.tenant_id}:{verification.public_id}:{verification.decision_revision}",
        algorithm="sha256",
    ).hexdigest()
    if int(digest, 16) % 10000 >= percent * 100:
        return None
    sample, created = ReviewQualityAssignment.objects.get_or_create(
        verification=verification,
        decision_revision=verification.decision_revision,
        defaults={
            "tenant_id": verification.tenant_id,
            "queue": entry.queue,
            "sampling_percent": percent,
            "original_outcome": decision.decision,
            "original_reason_codes": [
                code
                for code in decision.reason_codes_json
                if isinstance(code, str) and CODE.fullmatch(code)
            ],
            "maker_id": decision.decided_by_id,
            "checker_id": decision.approved_by_id,
            "required_skills": list(entry.required_skills),
        },
    )
    if created:
        record_audit_event(
            tenant=verification.tenant,
            action="review_quality.sampled",
            target_type="review_quality",
            target_id=sample.public_id,
            metadata={
                "verification_id": verification.public_id,
                "decision_revision": verification.decision_revision,
                "sampling_percent": percent,
            },
        )
        allocate_locked(sample)
    return sample


@transaction.atomic
def allocate_sample(sample, *, actor):
    lock_audit_chain(sample.tenant_id)
    sample = (
        visible_samples(actor)
        .select_for_update(of=("self",), no_key=True)
        .select_related("queue", "verification__verification_subject", "tenant")
        .filter(pk=sample.pk)
        .first()
    )
    if sample is None:
        raise NotFound("Quality review not found.")
    if (
        actor.tenant_id != sample.tenant_id
        or not sample.queue.members.filter(
            user=actor, available=True, deleted_at__isnull=True
        ).exists()
    ):
        raise ValidationError("Available queue membership is required.")
    return allocate_locked(sample)


@transaction.atomic
def complete_sample(sample, *, actor, outcome, reason_code, notes, request=None):
    lock_audit_chain(sample.tenant_id)
    case = (
        Verification.objects.select_for_update(of=("self",), no_key=True)
        .select_related("verification_subject", "tenant", "project")
        .get(pk=sample.verification_id)
    )
    if (
        case.deleted_at is not None
        or case.verification_subject.deleted_at is not None
        or case.tenant.deleted_at is not None
        or case.tenant.status != "active"
    ):
        raise NotFound("Quality review not found.")
    sample = (
        visible_samples(actor)
        .select_for_update(of=("self",), no_key=True)
        .select_related("queue", "verification__verification_subject")
        .filter(pk=sample.pk)
        .first()
    )
    if sample is None:
        raise NotFound("Quality review not found.")
    if sample.reviewer_id != actor.pk:
        raise ValidationError("This quality review is assigned to another reviewer.")
    member = (
        sample.queue.members.filter(user=actor, deleted_at__isnull=True)
        .select_related("user")
        .first()
    )
    if member is None or not quality_eligible(member, sample):
        raise ValidationError("Current independent reviewer eligibility is required.")
    from django.core.exceptions import ValidationError as ModelValidationError

    try:
        validate_reviewer_input(sample.verification, outcome, reason_code, notes)
    except ModelValidationError as exc:
        raise ValidationError({"reason_code": exc.messages}) from exc
    if sample.completed_at:
        if (
            sample.outcome == outcome
            and sample.reason_code == reason_code
            and sample.notes_json == {"notes": notes}
        ):
            return sample
        raise ValidationError("This quality review is already complete.")
    sample.outcome = outcome
    sample.reason_code = reason_code
    sample.notes_json = {"notes": notes}
    sample.completed_at = timezone.now()
    sample.save(
        update_fields=[
            "outcome",
            "reason_code",
            "notes_json",
            "completed_at",
            "updated_at",
        ]
    )
    record_audit_event(
        tenant=sample.tenant,
        actor=actor,
        request=request,
        action="review_quality.completed",
        target_type="review_quality",
        target_id=sample.public_id,
        metadata={
            "outcome": outcome,
            "agrees": outcome == sample.original_outcome,
            "reason_code": reason_code,
        },
    )
    return sample


def sample_summary(sample, *, actor=None):
    return {
        "id": sample.public_id,
        "can_review": actor is not None
        and sample.reviewer_id == actor.pk
        and sample.completed_at is None,
        "verification_id": sample.verification.public_id,
        "environment": sample.queue.environment,
        "decision_revision": sample.decision_revision,
        "original_outcome": sample.original_outcome,
        "original_reason_codes": sample.original_reason_codes,
        "reviewer_id": sample.reviewer.public_id if sample.reviewer_id else None,
        "outcome": sample.outcome or None,
        "reason_code": sample.reason_code or None,
        "completed_at": (
            sample.completed_at.isoformat() if sample.completed_at else None
        ),
        "agrees": (
            sample.outcome == sample.original_outcome if sample.completed_at else None
        ),
        "reason_rules": sample.verification.policy_snapshot_json.get(
            "review_reason_rules", {}
        ),
    }
