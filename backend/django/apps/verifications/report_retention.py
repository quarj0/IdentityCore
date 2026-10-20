"""Retire report objects without discarding failed deletion references."""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verifications.models import Verification
from apps.verifications.retention import has_active_retention_hold
from common.fields import environment_for_instance
from common.storage import delete_object, get_object_storage_evidence_bucket_name
from common.tenant_storage import PATTERN, resolve_reference

REPORT_FIELDS = {
    "json": "evidence_report_storage_key",
    "pdf": "evidence_report_pdf_storage_key",
}
REPORT_FLAGS = {
    "json": "evidence_report_encrypted",
    "pdf": "evidence_report_pdf_encrypted",
}
RETIRED = "evidence_reports_retired_at"
PENDING = "evidence_report_pending_cleanup_keys"


def report_due_at(verification):
    if verification.completed_at is None:
        return None
    try:
        policy = verification.policy_snapshot_json
        if not isinstance(policy, dict):
            return None
        days = policy.get("media_retention_days", 30)
        if isinstance(days, bool) or str(days) != str(int(days)) or int(days) < 1:
            return None
        return verification.completed_at + timedelta(days=int(days))
    except (ValueError, TypeError, OverflowError):
        return None


def report_allowed(verification):
    metadata = verification.metadata_json or {}
    if not isinstance(metadata, dict) or metadata.get(RETIRED):
        return False
    due = report_due_at(verification)
    if verification.completed_at is None:
        return True  # Legacy unknown completion time needs controlled reconciliation.
    if due is None:
        return False
    return due > timezone.now() or has_active_retention_hold(
        tenant_id=verification.tenant_id,
        verification_id=verification.pk,
        now=timezone.now(),
    )


def require_report_access(verification):
    if not report_allowed(verification):
        raise NotFound("Evidence report is no longer available.")


def report_reference(verification, key, kind):
    if kind not in REPORT_FIELDS or not isinstance(key, str):
        raise ValueError("Invalid report reference")
    suffix = (
        f"verifications/{verification.public_id}/reports/verification-report.{kind}"
    )
    if key.startswith("tenants/"):
        match = PATTERN.fullmatch(key)
        if match is None or match[4] != suffix:
            raise ValueError("Invalid report reference")
    elif key != f"organizations/{verification.organization.public_id}/{suffix}":
        raise ValueError("Invalid report reference")
    reference = resolve_reference(
        key,
        get_object_storage_evidence_bucket_name(),
        tenant_scope=verification.tenant.public_id,
        environment=environment_for_instance(verification),
    )
    if not reference["bucket"]:
        raise ValueError("Report storage unavailable")
    return reference


def remember_report_keys(metadata, keys):
    pending = metadata.get(PENDING, [])
    if not isinstance(pending, list) or len(pending) > 256:
        raise NotFound("Evidence report tracking is unavailable.")
    pending = list(pending)
    for kind, key in keys.items():
        previous = metadata.get(REPORT_FIELDS[kind])
        if previous and previous != key:
            item = {"format": kind, "key": previous}
            if item not in pending:
                pending.append(item)
        metadata[REPORT_FIELDS[kind]] = key
    if len(pending) > 256:
        raise NotFound("Evidence report tracking is unavailable.")
    if pending:
        metadata[PENDING] = pending


def retire_report_objects(verification, *, now=None):
    now = now or timezone.now()
    with transaction.atomic():
        lock_audit_chain(verification.tenant_id)
        current = (
            Verification.objects.select_for_update(of=("self",), no_key=True)
            .select_related("tenant", "organization", "project")
            .get(pk=verification.pk)
        )
        due = report_due_at(current)
        if (
            due is None
            or due > now
            or has_active_retention_hold(
                tenant_id=current.tenant_id, verification_id=current.pk, now=now
            )
        ):
            return False
        metadata = current.metadata_json or {}
        if (
            not isinstance(metadata, dict)
            or not isinstance(metadata.get(PENDING, []), list)
            or len(metadata.get(PENDING, [])) > 256
        ):
            record_audit_event(
                tenant=current.tenant,
                action="retention.evidence_report_deletion_failed",
                target_type="verification",
                target_id=current.public_id,
                metadata={"reason": "tracking_unavailable"},
            )
            return False
        metadata = dict(metadata)
        if not metadata.get(RETIRED):
            metadata[RETIRED] = now.isoformat()
            current.metadata_json = metadata
            current.save(update_fields=["metadata_json", "updated_at"])
        objects = [
            {"format": kind, "key": metadata[field]}
            for kind, field in REPORT_FIELDS.items()
            if field in metadata
        ]
        objects += list(metadata.get(PENDING) or [])
    deleted = False
    for item in objects:
        try:
            kind, key = item["format"], item["key"]
            reference = report_reference(current, key, kind)
            delete_object(bucket_name=reference["bucket"], key=key)
        except Exception:
            record_audit_event(
                tenant=current.tenant,
                action="retention.evidence_report_deletion_failed",
                target_type="verification",
                target_id=current.public_id,
                metadata={"reason": "storage_or_reference_unavailable"},
            )
            continue
        with transaction.atomic():
            lock_audit_chain(current.tenant_id)
            fresh = Verification.objects.select_for_update(
                of=("self",), no_key=True
            ).get(pk=current.pk)
            metadata = dict(fresh.metadata_json or {})
            if metadata.get(REPORT_FIELDS[kind]) == key:
                metadata.pop(REPORT_FIELDS[kind], None)
                metadata.pop(REPORT_FLAGS[kind], None)
            pending = [value for value in metadata.get(PENDING, []) if value != item]
            if pending:
                metadata[PENDING] = pending
            else:
                metadata.pop(PENDING, None)
            fresh.metadata_json = metadata
            fresh.save(update_fields=["metadata_json", "updated_at"])
            record_audit_event(
                tenant=current.tenant,
                action="retention.evidence_report_deleted",
                target_type="verification",
                target_id=current.public_id,
                metadata={"format": kind},
            )
        deleted = True
    return deleted


def refresh_pending_cleanup_deadlines(*, limit=100):
    """Recover after key outages without making revocation depend on decryption."""
    from django.db.models import F

    now = timezone.now()
    candidates = Verification.objects.filter(
        completed_at__isnull=False,
        media_cleanup_due_at__isnull=True,
        media_cleanup_completed_at__isnull=True,
    ).order_by(F("media_cleanup_attempted_at").asc(nulls_first=True), "pk")[:limit]
    for case in candidates:
        due = report_due_at(case)
        Verification.objects.filter(
            pk=case.pk,
            completed_at=case.completed_at,
            media_cleanup_due_at__isnull=True,
        ).update(media_cleanup_due_at=due, media_cleanup_attempted_at=now)
