from django.db.models import QuerySet

from apps.verifications.models import Verification


PLATFORM_REVIEW_WORKFLOWS = frozenset({"administrator_onboarding"})


def is_platform_owned_review(verification: Verification) -> bool:
    metadata = verification.metadata_json or {}
    return metadata.get("workflow") in PLATFORM_REVIEW_WORKFLOWS


def manual_review_queryset_for_user(user) -> QuerySet[Verification]:
    queryset = Verification.objects.select_related("tenant", "verification_subject")
    if getattr(user, "is_platform_admin", False):
        return queryset.filter(
            metadata_json__workflow__in=PLATFORM_REVIEW_WORKFLOWS,
        )
    if getattr(user, "tenant_id", None) is None:
        return queryset.none()
    return queryset.filter(tenant_id=user.tenant_id).exclude(
        metadata_json__workflow__in=PLATFORM_REVIEW_WORKFLOWS,
    )
