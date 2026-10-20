from celery import shared_task
from django.db.models import Exists, F, OuterRef, Q
from django.utils import timezone

from apps.evidence.lifecycle import retire_expired_resources
from apps.evidence.models import (
    Evidence,
    PurposeAuthorization,
    ResourceMaintenanceState,
)
from apps.tenants.models import Tenant


@shared_task
def retire_governed_resources_task(limit=100, tenant_limit=10):
    if (
        type(limit) is not int
        or not 1 <= limit <= 1000
        or type(tenant_limit) is not int
        or not 1 <= tenant_limit <= 100
    ):
        raise ValueError("Choose bounded resource and tenant batch sizes.")
    from apps.claims.models import Claim, ClaimDisclosure, ClaimResolution

    now = timezone.now()
    from apps.providers.models import ProviderCertification, ProviderOperation

    annotations = {}
    for index, (model, deadline) in enumerate(
        (
            (Evidence, "delete_after"),
            (Claim, "delete_after"),
            (PurposeAuthorization, "delete_after"),
            (ClaimDisclosure, "expires_at"),
            (ClaimResolution, "delete_after"),
            (ProviderCertification, "delete_after"),
            (ProviderOperation, "delete_after"),
        )
    ):
        annotations[f"has_due_{index}"] = Exists(
            model.objects.filter(
                tenant_id=OuterRef("pk"),
                deleted_at__isnull=True,
                **{deadline + "__lte": now},
            )
        )
    condition = Q()
    for key in annotations:
        condition |= Q(**{key: True})
    tenants = list(
        Tenant.objects.annotate(**annotations)
        .filter(condition)
        .order_by(
            F("resource_maintenance__last_examined_at").asc(nulls_first=True), "pk"
        )[:tenant_limit]
    )
    result = {"examined": 0, "failed": 0, "retired": 0}
    for tenant in tenants:
        error_code = ""
        try:
            counts = retire_expired_resources(tenant_id=tenant.pk, limit=limit)
            from apps.providers.maintenance import retire_provider_records

            provider_counts = retire_provider_records(tenant_id=tenant.pk, limit=limit)
            result["retired"] += sum(
                value for key, value in provider_counts.items() if key != "held"
            )
            result["retired"] += sum(
                value for key, value in counts.items() if key != "held"
            )
        except Exception as exc:
            # Record no payload, key-provider detail or credential-bearing text.
            error_code = type(exc).__name__[:120]
            result["failed"] += 1
        ResourceMaintenanceState.objects.update_or_create(
            tenant=tenant,
            defaults={
                "last_examined_at": timezone.now(),
                "last_error_code": error_code,
            },
        )
        result["examined"] += 1
    return result
