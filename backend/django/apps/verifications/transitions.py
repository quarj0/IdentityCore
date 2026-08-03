from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.verifications.models import Verification, VerificationStatus


class VerificationTransitionError(ValueError):
    """Raised when a verification status change is not in the state table."""


TERMINAL_STATUSES = frozenset(
    {
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.EXPIRED,
        VerificationStatus.CANCELLED,
        VerificationStatus.FAILED,
    }
)


ALLOWED_TRANSITIONS = {
    VerificationStatus.CREATED: frozenset(
        {VerificationStatus.PENDING_CONSENT, VerificationStatus.CANCELLED, VerificationStatus.EXPIRED}
    ),
    VerificationStatus.PENDING_CONSENT: frozenset(
        {
            VerificationStatus.IN_PROGRESS,
            VerificationStatus.CANCELLED,
            VerificationStatus.EXPIRED,
            VerificationStatus.FAILED,
        }
    ),
    VerificationStatus.IN_PROGRESS: frozenset(
        {
            VerificationStatus.AWAITING_DOCUMENT,
            VerificationStatus.AWAITING_SELFIE,
            VerificationStatus.PROCESSING,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
            VerificationStatus.CANCELLED,
            VerificationStatus.EXPIRED,
            VerificationStatus.FAILED,
        }
    ),
    VerificationStatus.AWAITING_DOCUMENT: frozenset(
        {
            VerificationStatus.AWAITING_SELFIE,
            VerificationStatus.PROCESSING,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
            VerificationStatus.CANCELLED,
            VerificationStatus.EXPIRED,
            VerificationStatus.FAILED,
        }
    ),
    VerificationStatus.AWAITING_SELFIE: frozenset(
        {
            VerificationStatus.AWAITING_DOCUMENT,
            VerificationStatus.PROCESSING,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
            VerificationStatus.CANCELLED,
            VerificationStatus.EXPIRED,
            VerificationStatus.FAILED,
        }
    ),
    VerificationStatus.PROCESSING: frozenset(
        {
            VerificationStatus.AWAITING_DOCUMENT,
            VerificationStatus.AWAITING_SELFIE,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.CANCELLED,
            VerificationStatus.EXPIRED,
            VerificationStatus.FAILED,
        }
    ),
    VerificationStatus.MANUAL_REVIEW_REQUIRED: frozenset(
        {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.FAILED,
        }
    ),
}


def _status_value(status: str | VerificationStatus) -> str:
    return status.value if isinstance(status, VerificationStatus) else status


@transaction.atomic
def transition_verification(
    verification: Verification,
    target_status: str | VerificationStatus,
    *,
    completed_at: datetime | None = None,
    clear_completed_at: bool = False,
) -> tuple[Verification, bool]:
    """Apply one state transition while serializing concurrent writers.

    Repeating the current transition is an idempotent no-op. Every other
    transition must be present in ``ALLOWED_TRANSITIONS`` and is applied while
    holding a row lock. Callers can use the returned locked instance when they
    need to make additional changes in the same transaction.
    """

    target = _status_value(target_status)
    current = (
        Verification.objects.select_for_update()
        .select_related("tenant", "verification_subject")
        .get(pk=verification.pk)
    )
    if current.status == target:
        verification.status = current.status
        verification.completed_at = current.completed_at
        verification.updated_at = current.updated_at
        return current, False
    if target not in ALLOWED_TRANSITIONS.get(current.status, frozenset()):
        raise VerificationTransitionError(
            f"Cannot transition verification from {current.status!r} to {target!r}."
        )

    now = completed_at or timezone.now()
    current.status = target
    fields = ["status", "updated_at"]
    if target in TERMINAL_STATUSES:
        current.completed_at = now
        fields.append("completed_at")
    elif clear_completed_at:
        current.completed_at = None
        fields.append("completed_at")
    current.save(update_fields=fields)
    verification.status = current.status
    verification.completed_at = current.completed_at
    verification.updated_at = current.updated_at
    return current, True
