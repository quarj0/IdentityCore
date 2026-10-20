"""Bounded retirement and durable remote cancel/delete reconciliation."""

from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.audit.services import lock_audit_chain
from apps.evidence.access import protected_value
from apps.evidence.lifecycle import active_subject_holds
from apps.evidence.services import _audit, _transition
from apps.providers.configuration import _signing_context
from apps.providers.http_adapter import SecureHTTPProviderAdapter
from apps.providers.models import ProviderCertification, ProviderOperation
from apps.providers.operations import _related, envelope

REMOTE_CONTROL_WINDOW = timedelta(days=30)


@transaction.atomic
def retire_provider_records(*, tenant_id, limit=100):
    lock_audit_chain(tenant_id)
    now = timezone.now()
    result = {"operations": 0, "certifications": 0, "held": 0}
    # Separate limits prevent a busy operation queue from starving expired reports.
    for record in (
        ProviderCertification.objects.filter(
            tenant_id=tenant_id,
            delete_after__lte=now,
            deleted_at__isnull=True,
        )
        .select_related("tenant", "configuration")
        .order_by("delete_after", "pk")[:limit]
    ):
        _transition(
            record,
            report_json={},
            deleted_at=now,
            revoked_at=record.revoked_at or now,
            revocation_reason=record.revocation_reason or "retention_expired",
        )
        _audit(record, None, "provider.certification_retired")
        result["certifications"] += 1
    # Exclude held subjects before LIMIT so a held operation cannot starve others.
    from django.db.models import Exists, OuterRef
    from apps.evidence.models import ResourceLegalHold
    from apps.verifications.models import RetentionLegalHold

    live = Q(released_at__isnull=True) & (
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    governed_holds = ResourceLegalHold.objects.filter(
        live,
        tenant_id=tenant_id,
        project_id=OuterRef("project_id"),
        subject_id=OuterRef("verification__verification_subject_id"),
    )
    legacy_holds = RetentionLegalHold.objects.filter(live).filter(
        Q(tenant_id=tenant_id, verification__isnull=True)
        | Q(verification_id=OuterRef("verification_id"))
    )
    due = (
        _related()
        .filter(tenant_id=tenant_id, delete_after__lte=now, deleted_at__isnull=True)
        .annotate(
            governed_held=Exists(governed_holds),
            legacy_held=Exists(legacy_holds),
        )
        .filter(governed_held=False, legacy_held=False)
        .order_by("delete_after", "pk")[:limit]
    )
    for record in due:
        if active_subject_holds(
            record.verification.verification_subject, record.project, now=now
        ):
            result["held"] += 1
            continue
        _transition(
            record,
            result_json={},
            result_sha256="",
            deleted_at=now,
            status="cancelled",
            invalidation_reason="retention_expired",
            completed_at=record.completed_at or now,
            remote_action="delete",
            remote_action_status="pending",
            remote_requested_at=now,
        )
        _audit(record, None, "provider.operation_retired")
        result["operations"] += 1
    return result


def reconcile_remote_action(operation_id):
    """Return an acknowledgement only after matching a signed exact-scope receipt."""
    reference = (
        ProviderOperation.objects.only("tenant_id")
        .filter(public_id=operation_id)
        .first()
    )
    if reference is None:
        return "unavailable"
    with transaction.atomic():
        lock_audit_chain(reference.tenant_id)
        record = _related().get(public_id=operation_id)
        if record.remote_action_status != "pending":
            return record.remote_action_status
        now = timezone.now()
        if record.remote_attempted_at and record.remote_attempted_at > now - timedelta(
            minutes=5
        ):
            return "pending"
        if now >= (
            record.remote_requested_at or record.deadline
        ) + REMOTE_CONTROL_WINDOW or not protected_value(record, "lease_json"):
            _transition(record, remote_action_status="expired", lease_json={})
            _audit(
                record,
                None,
                "provider.remote_control_expired",
                remote_action=record.remote_action,
            )
            return "expired"
        action = record.remote_action
        binding = envelope(record)
        config = record.configuration
        _transition(record, remote_attempted_at=now)
    # Even after local erasure the encrypted random lease remains for this bounded
    # remote-cleanup window. It contains no subject values and is cleared on ack.
    accepted = False
    try:
        response = SecureHTTPProviderAdapter(
            config.public_configuration_json
        ).post_json(
            url=config.public_configuration_json["endpoint_url"],
            payload={"contract_version": "1", "operation": action, "binding": binding},
            headers={"Authorization": "Bearer " + config.credentials_json["api_key"]},
            signing=_signing_context(config),
        )
        accepted = response == {
            "binding": binding,
            "status": "deleted" if action == "delete" else "cancelled",
        }
    except Exception:
        # Do not persist provider response text, endpoint errors, credentials or data.
        accepted = False
    with transaction.atomic():
        lock_audit_chain(reference.tenant_id)
        record = _related().get(public_id=operation_id)
        if record.remote_action != action or record.remote_action_status != "pending":
            return record.remote_action_status
        if accepted:
            fields = {"remote_action_status": "acknowledged"}
            if action == "delete":
                fields["lease_json"] = {}
            _transition(record, **fields)
            _audit(
                record,
                None,
                "provider.remote_control_acknowledged",
                remote_action=action,
            )
    return "acknowledged" if accepted else "pending"


@shared_task
def reconcile_provider_controls_task(limit=100):
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Choose a bounded provider-control batch size.")
    now = timezone.now()
    identifiers = list(
        ProviderOperation.objects.filter(remote_action_status="pending")
        .filter(
            Q(remote_attempted_at__isnull=True)
            | Q(remote_attempted_at__lte=now - timedelta(minutes=5))
        )
        .order_by(F("remote_attempted_at").asc(nulls_first=True), "pk")
        .values_list("public_id", flat=True)[:limit]
    )
    result = {"examined": 0, "acknowledged": 0, "expired": 0, "failed": 0}
    for public_id in identifiers:
        result["examined"] += 1
        try:
            outcome = reconcile_remote_action(public_id)
            if outcome in {"acknowledged", "expired"}:
                result[outcome] += 1
        except Exception:
            result["failed"] += 1
            # A broken key-provider entry must not starve later records forever.
            with transaction.atomic():
                reference = ProviderOperation.objects.only("tenant_id").get(
                    public_id=public_id
                )
                lock_audit_chain(reference.tenant_id)
                record = ProviderOperation.objects.get(public_id=public_id)
                _transition(record, remote_attempted_at=timezone.now())
    return result
