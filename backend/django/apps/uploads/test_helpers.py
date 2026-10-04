"""Seal synthetic prevalidated uploads in backend fixtures; never production input."""

from apps.uploads.models import UploadStatus
from apps.uploads.provenance import issue_receipt


def seal_test_upload(upload):
    if upload.status in {
        UploadStatus.UPLOADED,
        UploadStatus.CONSUMED,
        UploadStatus.PROMOTED,
    }:
        upload.capture_provenance_version = 1
        upload.capture_receipt = issue_receipt(upload)
        upload.save(update_fields=["capture_provenance_version", "capture_receipt"])
    return upload
