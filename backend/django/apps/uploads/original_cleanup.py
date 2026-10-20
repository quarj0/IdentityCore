"""Owned cleanup of legacy direct objects after immutable upload finalization."""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.uploads.models import Upload
from apps.uploads.services import PURPOSE_STORAGE_SEGMENT
from apps.verifications.models import Verification
from apps.verifications.retention import has_active_retention_hold
from common.fields import environment_for_instance
from common.storage import delete_object, get_object_storage_temp_bucket_name
from common.tenant_storage import PATTERN, resolve_reference

logger = logging.getLogger(__name__)
# Signed legacy PUTs may still be writable. Keep a sweep reference beyond expiry;
# deployment storage timeouts and reconciliation cover uncertain/paused writes.
ORIGINAL_WRITE_GRACE = timedelta(minutes=5)


def _reference(upload, key):
    segment = PURPOSE_STORAGE_SEGMENT.get(upload.purpose)
    suffix = (
        f"verifications/{upload.verification.public_id}/{segment}/{upload.public_id}"
    )
    if not segment or key == upload.storage_key:
        raise ValueError("Original upload reference is unavailable.")
    if key.startswith("tenants/"):
        match = PATTERN.fullmatch(key)
        if match is None or match[4] != suffix:
            raise ValueError("Original upload reference is unavailable.")
    elif key != f"organizations/{upload.verification.organization.public_id}/{suffix}":
        raise ValueError("Original upload reference is unavailable.")
    reference = resolve_reference(
        key,
        get_object_storage_temp_bucket_name(),
        tenant_scope=upload.tenant.public_id,
        environment=environment_for_instance(upload),
    )
    if not reference["bucket"]:
        raise ValueError("Temporary upload storage is unavailable.")
    return reference


def cleanup_original_upload(upload, *, immediate=False):
    try:
        with transaction.atomic():
            lock_audit_chain(upload.tenant_id)
            case = Verification.objects.select_for_update(no_key=True).get(
                pk=upload.verification_id
            )
            current = (
                Upload.objects.select_for_update(of=("self",))
                .select_related(
                    "tenant", "verification__organization", "verification__project"
                )
                .get(pk=upload.pk)
            )
            if (
                current.tenant_id != case.tenant_id
                or current.verification_id != case.pk
            ):
                raise ValueError("Original upload ownership changed.")
            key = current.original_storage_key
            if not key or (
                not immediate
                and timezone.now() < current.expires_at + ORIGINAL_WRITE_GRACE
            ):
                return False
            if has_active_retention_hold(
                tenant_id=current.tenant_id, verification_id=case.pk, now=timezone.now()
            ):
                return False
            reference = _reference(current, key)
            current.original_cleanup_attempted_at = timezone.now()
            current.save(update_fields=["original_cleanup_attempted_at", "updated_at"])
        delete_object(bucket_name=reference["bucket"], key=key)
        with transaction.atomic():
            lock_audit_chain(upload.tenant_id)
            current = Upload.objects.select_for_update().get(pk=upload.pk)
            resweep = timezone.now() < current.expires_at + ORIGINAL_WRITE_GRACE
            if current.original_storage_key == key and not resweep:
                current.original_storage_key = ""
                current.save(update_fields=["original_storage_key", "updated_at"])
            record_audit_event(
                tenant=current.tenant,
                action="upload.original_temporary_object_deleted",
                target_type="upload",
                target_id=current.public_id,
                metadata={"resweep_required": resweep},
            )
        return True
    except Exception as exc:
        logger.warning(
            "Original upload cleanup deferred upload=%s error=%s",
            upload.public_id,
            type(exc).__name__,
        )
        return False
