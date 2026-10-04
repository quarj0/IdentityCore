"""Server-attested media bindings; browser capture methods are untrusted claims."""

from django.core import signing
from rest_framework.exceptions import ValidationError

from apps.uploads.models import Upload, UploadStatus

SALT = "identitycore.capture-receipt.v1"


def _binding(upload):
    return {
        "version": 1,
        "tenant": str(upload.tenant_id),
        "verification": str(upload.verification_id),
        "session": str(upload.verification_session_id),
        "upload": str(upload.pk),
        "purpose": upload.purpose,
        "checksum": upload.checksum_sha256,
        "reported_method": upload.capture_method,
    }


def issue_receipt(upload):
    return signing.dumps(_binding(upload), salt=SALT)


def validate_receipt(upload):
    if not upload.capture_receipt and upload.capture_provenance_version == 0:
        return False  # Legacy evidence is unverified, never attested retroactively.
    if upload.capture_provenance_version != 1:
        raise ValidationError(
            {"upload_id": "Capture provenance version is unsupported."}
        )
    try:
        payload = signing.loads(upload.capture_receipt, salt=SALT)
    except (signing.BadSignature, ValueError, TypeError) as exc:
        raise ValidationError(
            {"upload_id": "Capture provenance could not be verified."}
        ) from exc
    if payload != _binding(upload):
        raise ValidationError(
            {"upload_id": "Capture provenance does not match this evidence."}
        )
    return True


def capture_signals(verification):
    counts = {
        "attested": 0,
        "legacy_unverified": 0,
        "invalid": 0,
        "reported_camera": 0,
        "reported_live_recording": 0,
        "file_fallback": 0,
        "unreported": 0,
        "media_reuse": 0,
    }
    uploads = list(
        Upload.objects.filter(
            tenant=verification.tenant,
            verification=verification,
            deleted_at__isnull=True,
            status__in=[UploadStatus.CONSUMED, UploadStatus.PROMOTED],
        ).order_by("-created_at", "-pk")[:101]
    )
    truncated = len(uploads) > 100
    uploads = uploads[:100]
    checksums = {u.checksum_sha256 for u in uploads if u.checksum_sha256}
    reused = set(
        Upload.objects.filter(
            tenant=verification.tenant,
            deleted_at__isnull=True,
            checksum_sha256__in=checksums,
            status__in=[
                UploadStatus.UPLOADED,
                UploadStatus.CONSUMED,
                UploadStatus.PROMOTED,
            ],
        )
        .exclude(verification=verification)
        .values_list("checksum_sha256", flat=True)
        .distinct()
    )
    for upload in uploads:
        try:
            verified = validate_receipt(upload)
        except ValidationError:
            counts["invalid"] += 1
            continue
        counts["attested" if verified else "legacy_unverified"] += 1
        method = {
            "camera": "reported_camera",
            "live_recording": "reported_live_recording",
            "file": "file_fallback",
        }.get(upload.capture_method, "unreported")
        counts[method] += 1
        if upload.checksum_sha256 in reused:
            counts["media_reuse"] += 1
    return {
        "version": "capture-provenance-v1",
        "client_metadata_trusted": False,
        "truncated": truncated,
        **counts,
    }
