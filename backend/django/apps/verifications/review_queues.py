"""Tenant-serialized queue admission and least-loaded reviewer assignment."""

from datetime import timedelta
import re

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verifications.models import (
    ReviewQueue,
    ReviewQueueEntry,
    Verification,
    VerificationReviewOwner,
    VerificationStatus,
)
from apps.verifications.review_access import can_review_verification

SKILL = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")


def validate_list(value, pattern, label):
    if (
        not isinstance(value, list)
        or len(value) > 100
        or any(
            not isinstance(item, str) or not pattern.fullmatch(item) for item in value
        )
        or len(set(value)) != len(value)
    ):
        raise ValidationError({label: "Use at most 100 unique valid codes."})
    return value


def case_environment(case):
    return case.project.environment if case.project_id else "sandbox"


def document_country(case):
    document = (
        case.identity_documents.filter(deleted_at__isnull=True)
        .order_by("-created_at", "-pk")
        .first()
    )
    classification = (
        (document.extracted_data_json or {}).get("document_classification", {})
        if document
        else {}
    )
    country = (
        classification.get("predicted_country_code", "")
        if isinstance(classification, dict)
        else ""
    )
    return country if isinstance(country, str) and COUNTRY.fullmatch(country) else ""


def admit_locked(case):
    if (
        case.review_owner != VerificationReviewOwner.TENANT
        or case.status != VerificationStatus.MANUAL_REVIEW_REQUIRED
        or case.deleted_at is not None
    ):
        return None
    existing = ReviewQueueEntry.objects.filter(verification=case).first()
    if existing:
        return existing
    country = document_country(case)
    queues = ReviewQueue.objects.filter(
        tenant_id=case.tenant_id,
        environment=case_environment(case),
        active=True,
        deleted_at__isnull=True,
    ).order_by("-priority", "created_at", "pk")
    for queue in queues:
        if queue.country_codes and country not in queue.country_codes:
            continue
        return ReviewQueueEntry.objects.create(
            verification=case,
            queue=queue,
            priority=queue.priority,
            due_at=(case.review_queued_at or case.created_at)
            + timedelta(minutes=queue.sla_minutes),
            country_code=country,
            required_skills=list(queue.required_skills),
        )
    return None


@transaction.atomic
def admit_tenant(tenant_id, environment):
    lock_audit_chain(tenant_id)
    cases = Verification.objects.filter(
        tenant_id=tenant_id,
        status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        review_owner=VerificationReviewOwner.TENANT,
        deleted_at__isnull=True,
        queue_entry__isnull=True,
    )
    if environment == "sandbox":
        from django.db.models import Q

        cases = cases.filter(
            Q(project__environment=environment) | Q(project__isnull=True)
        )
    else:
        cases = cases.filter(project__environment=environment)
    for case in (
        cases.select_for_update(of=("self",), no_key=True)
        .select_related("project")
        .order_by("created_at", "pk")
        .iterator(chunk_size=100)
    ):
        admit_locked(case)


def eligible(member, case, skills):
    user = member.user
    return (
        member.available
        and member.deleted_at is None
        and user.is_active
        and user.status == "active"
        and user.deleted_at is None
        and user.tenant_id == case.tenant_id
        and not user.is_platform_admin
        and can_review_verification(user, case)
        and set(skills).issubset(set(member.skills))
        and case.created_by_id != user.pk
        and (
            not user.email
            or user.email.strip().lower()
            != (case.verification_subject.email or "").strip().lower()
        )
    )


@transaction.atomic
def assign_next(queue, *, actor, request=None):
    lock_audit_chain(queue.tenant_id)
    queue = ReviewQueue.objects.select_for_update().get(pk=queue.pk)
    if (
        actor.tenant_id != queue.tenant_id
        or actor.is_platform_admin
        or not actor.is_active
        or queue.tenant.status != "active"
        or queue.tenant.deleted_at is not None
    ):
        raise ValidationError("Active tenant reviewer access is required.")
    if not queue.active or queue.deleted_at is not None:
        raise ValidationError("The queue is inactive.")
    if not queue.members.filter(
        user=actor, available=True, deleted_at__isnull=True
    ).exists():
        raise ValidationError("You are not an available member of this queue.")
    admit_tenant(queue.tenant_id, queue.environment)
    entries = (
        ReviewQueueEntry.objects.filter(
            queue=queue,
            verification__status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            verification__assigned_reviewer__isnull=True,
            verification__deleted_at__isnull=True,
        )
        .select_related("verification__verification_subject", "verification__project")
        .order_by("-priority", "due_at", "created_at", "pk")
    )
    members = list(
        queue.members.select_for_update()
        .filter(deleted_at__isnull=True)
        .select_related("user")
    )
    for entry in entries.iterator(chunk_size=100):
        case = (
            Verification.objects.select_for_update(of=("self",), no_key=True)
            .select_related("verification_subject", "project")
            .get(pk=entry.verification_id)
        )
        if (
            case.assigned_reviewer_id is not None
            or case.status != VerificationStatus.MANUAL_REVIEW_REQUIRED
            or case.review_owner != VerificationReviewOwner.TENANT
            or case_environment(case) != queue.environment
        ):
            continue
        candidates = [
            member
            for member in members
            if eligible(member, case, entry.required_skills)
        ]
        if not candidates:
            continue

        def fairness(member):
            workload = Verification.objects.filter(
                tenant_id=queue.tenant_id,
                assigned_reviewer_id=member.user_id,
                status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
                deleted_at__isnull=True,
            )
            if queue.environment == "sandbox":
                from django.db.models import Q

                workload = workload.filter(
                    Q(project__environment="sandbox") | Q(project__isnull=True)
                )
            else:
                workload = workload.filter(project__environment="production")
            load = workload.count()
            return (
                load,
                member.last_assigned_at
                or timezone.datetime.min.replace(
                    tzinfo=timezone.get_current_timezone()
                ),
                member.user_id,
            )

        chosen = min(candidates, key=fairness)
        now = timezone.now()
        case.assigned_reviewer = chosen.user
        case.assigned_at = now
        case.save(update_fields=["assigned_reviewer", "assigned_at", "updated_at"])
        chosen.last_assigned_at = now
        chosen.save(update_fields=["last_assigned_at", "updated_at"])
        record_audit_event(
            tenant=case.tenant,
            actor=actor,
            request=request,
            action="verification.review_assigned",
            target_type="verification",
            target_id=case.public_id,
            metadata={
                "reviewer_id": chosen.user.public_id,
                "queue_id": queue.public_id,
            },
        )
        return case
    return None


def entry_summary(entry):
    return {
        "verification_id": entry.verification.public_id,
        "queue_id": entry.queue.public_id,
        "priority": entry.priority,
        "due_at": entry.due_at.isoformat(),
        "overdue": entry.due_at < timezone.now(),
        "country_code": entry.country_code,
        "required_skills": entry.required_skills,
        "assigned_reviewer_id": (
            entry.verification.assigned_reviewer.public_id
            if entry.verification.assigned_reviewer_id
            else None
        ),
    }
