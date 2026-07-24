from django.db.models import QuerySet

from apps.verifications.models import Verification, VerificationReviewOwner


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
    if getattr(user, "is_platform_admin", False):
        return queryset.filter(review_owner=VerificationReviewOwner.PLATFORM)
    if getattr(user, "tenant_id", None) is None:
        return queryset.none()
    return queryset.filter(
        tenant_id=user.tenant_id,
        review_owner=VerificationReviewOwner.TENANT,
    )
