from django.db.models import QuerySet

from apps.verifications.models import Verification, VerificationReviewOwner
from common.authorization import AuthorizationAction, decide_user_access

PLATFORM_REVIEW_WORKFLOWS = frozenset({"administrator_onboarding"})


def review_owner_for_metadata(metadata: dict | None) -> str:
    workflow = (metadata or {}).get("workflow")
    if workflow in PLATFORM_REVIEW_WORKFLOWS:
        return VerificationReviewOwner.PLATFORM
    return VerificationReviewOwner.TENANT


def is_platform_owned_review(verification: Verification) -> bool:
    return verification.review_owner == VerificationReviewOwner.PLATFORM


def manual_review_queryset_for_user(user) -> QuerySet[Verification]:
    queryset = Verification.objects.select_related("tenant", "verification_subject")
    if decide_user_access(
        user,
        action=AuthorizationAction.MANUAL_REVIEW,
        review_owner=VerificationReviewOwner.PLATFORM,
    ).allowed:
        return queryset.filter(review_owner=VerificationReviewOwner.PLATFORM)
    if not decide_user_access(
        user,
        action=AuthorizationAction.MANUAL_REVIEW,
        tenant=getattr(user, "tenant_id", None),
        review_owner=VerificationReviewOwner.TENANT,
    ).allowed:
        return queryset.none()
    return queryset.filter(
        tenant_id=user.tenant_id,
        review_owner=VerificationReviewOwner.TENANT,
    )


def can_review_verification(user, verification: Verification) -> bool:
    return decide_user_access(
        user,
        action=AuthorizationAction.MANUAL_REVIEW,
        tenant=verification.tenant_id,
        review_owner=verification.review_owner,
    ).allowed


def can_approve_review(user, verification, decision) -> bool:
    """Current presentation hint; approval rechecks these constraints under lock."""
    from apps.verifications.models import VerificationApprovalStatus

    if not decision or decision.approval_status != VerificationApprovalStatus.PENDING:
        return False
    if verification.status != "manual_review_required" or not can_review_verification(
        user, verification
    ):
        return False
    if decision.decided_by_id == getattr(
        user, "pk", None
    ) or verification.created_by_id == getattr(user, "pk", None):
        return False
    reviewer_email = (getattr(user, "email", "") or "").strip().lower()
    subject_email = (verification.verification_subject.email or "").strip().lower()
    return not (reviewer_email and reviewer_email == subject_email)
