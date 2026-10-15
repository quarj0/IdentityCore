"""Production-only provider usage reconciliation; deliberately unrated.

This is an operator-controlled accounting primitive, not a payment processor.
Recorded events cannot charge or suspend organizations. Provider scope refers
to ownership, not a price: platform-owned != necessarily built-in/managed AI.
"""
from django.db import transaction

from apps.billing.models import BillingUsageEvent
from apps.providers.models import ProviderCheck, ProviderCheckStatus

METERABLE_RESULTS = {
    ProviderCheckStatus.COMPLETED,
    ProviderCheckStatus.FAILED,
    ProviderCheckStatus.TIMEOUT,
}


class BillingIntegrityError(ValueError):
    pass


@transaction.atomic
def record_provider_usage(provider_check_id):
    """Return (event, created), or (None, False) for incomplete/sandbox work.

    Uses a locked source row and a unique provider_check foreign key so repeated
    processing/reconciliation cannot silently duplicate a usage fact.
    """
    check = (
        ProviderCheck.objects.select_for_update()
        .select_related("verification__project", "verification__tenant", "provider")
        .get(pk=provider_check_id)
    )
    verification = check.verification
    project = verification.project
    if check.status not in METERABLE_RESULTS or not check.completed_at:
        return None, False

    if (
        check.tenant_id != verification.tenant_id
        or verification.tenant.organization_id != verification.organization_id
        or (project is not None and project.tenant_id != check.tenant_id)
        or check.provider.tenant_id not in (None, check.tenant_id)
    ):
        raise BillingIntegrityError("Tenant/provider attribution mismatch")

    # Never create a ledger fact for sandbox, unprojected or unknown work.
    if project is None or project.environment != "production":
        return None, False

    scope = "tenant_owned" if check.provider.tenant_id else "platform"
    defaults = {
        "tenant_id": check.tenant_id,
        "project_id": project.pk,
        "environment": "production",
        "capability": check.check_type,
        "provider_scope": scope,
        "outcome": check.status,
        "occurred_at": check.completed_at,
        "quantity": 1,
        "rating_state": "unrated",
    }
    event, created = BillingUsageEvent.objects.get_or_create(
        provider_check=check, defaults=defaults
    )
    if not created and any(getattr(event, key) != value for key, value in defaults.items()):
        # A late correction must be reconciled explicitly, not silently
        # rewritten as a different chargeable observation.
        raise BillingIntegrityError("Recorded usage has changed; manual correction required")
    return event, created
