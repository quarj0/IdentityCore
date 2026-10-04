"""Versioned authenticity evidence and source-coordinate suspicious regions."""

import json
import math
from io import BytesIO

from PIL import Image, ImageOps
from django.db import DatabaseError

from apps.providers.adapters import ProviderContractError
from apps.audit.services import record_audit_event
from apps.providers.models import ProviderCheckType
from apps.providers.services import (
    execute_provider_route,
    invoke_selected_provider_operation,
)
from apps.verifications.processing_jobs import ProcessingJobOwnershipLost
from common.storage import (
    get_object_bytes,
    get_object_storage_temp_bucket_name,
    get_object_storage_media_bucket_name,
)

REASONS = {
    "copy_move",
    "resampling",
    "text_inconsistency",
    "portrait_edit",
    "template_inconsistency",
}
FIELDS = {
    "contract_version",
    "capability",
    "status",
    "authenticity_version",
    "verdict",
    "confidence",
    "model_name",
    "model_version",
    "source_size",
    "analysis_size",
    "analysis_to_source",
    "regions",
    "raw_output",
}


def unavailable_authenticity(*, source_size, **kwargs):
    """No calibrated managed model is currently shipped; uncertainty requires review."""
    return {
        "contract_version": "1",
        "capability": "document_authenticity",
        "status": "inconclusive",
        "authenticity_version": "1",
        "verdict": "inconclusive",
        "confidence": None,
        "model_name": "unavailable",
        "model_version": "1",
        "source_size": list(source_size),
        "analysis_size": list(source_size),
        "analysis_to_source": [1, 0, 0, 0, 1, 0],
        "regions": [],
        "raw_output": {"reason": "authenticity_model_unavailable"},
    }


def normalize_authenticity(result, *, source_size):
    def invalid():
        raise ProviderContractError("Invalid document authenticity evidence v1.")

    def number(value, *, minimum=None, maximum=None):
        if (
            type(value) not in {int, float}
            or not math.isfinite(value)
            or (minimum is not None and value < minimum)
            or (maximum is not None and value > maximum)
        ):
            invalid()
        return float(value)

    if (
        not isinstance(result, dict)
        or set(result) != FIELDS
        or result["contract_version"] != "1"
        or result["authenticity_version"] != "1"
        or result["capability"] != "document_authenticity"
    ):
        invalid()
    if (
        not isinstance(result["status"], str)
        or not isinstance(result["verdict"], str)
        or result["status"] not in {"completed", "inconclusive"}
        or result["verdict"] not in {"authentic", "suspicious", "inconclusive"}
    ):
        invalid()
    if (result["status"] == "inconclusive") != (result["verdict"] == "inconclusive"):
        invalid()
    confidence = (
        None
        if result["verdict"] == "inconclusive"
        else number(result["confidence"], minimum=0, maximum=1)
    )
    if result["verdict"] == "inconclusive" and result["confidence"] is not None:
        invalid()
    for field in ("model_name", "model_version"):
        if (
            not isinstance(result[field], str)
            or not 1 <= len(result[field]) <= 64
            or any(
                not (c.isascii() and (c.isalnum() or c in "_.-")) for c in result[field]
            )
        ):
            invalid()
    for field in ("source_size", "analysis_size"):
        size = result[field]
        if (
            not isinstance(size, list)
            or len(size) != 2
            or any(type(d) is not int or not 1 <= d <= 32768 for d in size)
        ):
            invalid()
    if tuple(result["source_size"]) != tuple(source_size):
        invalid()
    matrix = result["analysis_to_source"]
    if not isinstance(matrix, list) or len(matrix) != 6:
        invalid()
    a, b, c, d, e, f = [number(v, minimum=-32768, maximum=32768) for v in matrix]
    if abs(a * e - b * d) < 1e-12:
        invalid()
    regions = result["regions"]
    if not isinstance(regions, list) or len(regions) > 20:
        invalid()
    normalized = []
    width, height = source_size
    aw, ah = result["analysis_size"]
    for region in regions:
        if (
            not isinstance(region, dict)
            or set(region) != {"box", "reason", "confidence"}
            or not isinstance(region["reason"], str)
            or region["reason"] not in REASONS
        ):
            invalid()
        box = region["box"]
        if not isinstance(box, list) or len(box) != 4:
            invalid()
        x, y, w, h = [number(v, minimum=0) for v in box]
        if w <= 0 or h <= 0 or x + w > aw or y + h > ah:
            invalid()
        corners = [
            (a * px + b * py + c, d * px + e * py + f)
            for px, py in ((x, y), (x + w, y), (x, y + h), (x + w, y + h))
        ]
        if any(
            px < -1e-6 or py < -1e-6 or px > width + 1e-6 or py > height + 1e-6
            for px, py in corners
        ):
            invalid()
        left, top = max(0, min(p[0] for p in corners)), max(
            0, min(p[1] for p in corners)
        )
        right, bottom = min(width, max(p[0] for p in corners)), min(
            height, max(p[1] for p in corners)
        )
        normalized.append(
            {
                "box": [
                    left / width,
                    top / height,
                    (right - left) / width,
                    (bottom - top) / height,
                ],
                "reason": region["reason"],
                "confidence": number(region["confidence"], minimum=0, maximum=1),
            }
        )
    try:
        raw = json.dumps(result["raw_output"], allow_nan=False)
    except (ValueError, TypeError, RecursionError):
        invalid()
    if not isinstance(result["raw_output"], dict) or len(raw.encode()) > 65536:
        invalid()
    return {
        **result,
        "confidence": confidence,
        "regions": normalized,
        "coordinate_space": "source_normalized",
    }


def source_size_for_capture(capture):
    from apps.uploads.models import Upload

    if (
        capture.deleted_at
        or capture.status == "deleted"
        or capture.identity_document.deleted_at
        or capture.identity_document.verification.deleted_at
        or capture.identity_document.verification_subject.deleted_at
    ):
        raise ProviderContractError("Document capture is unavailable.")
    upload = Upload.objects.filter(
        tenant_id=capture.tenant_id,
        verification_id=capture.identity_document.verification_id,
        storage_key=capture.storage_key,
        deleted_at__isnull=True,
        purpose="document_capture",
        status__in=["consumed", "promoted"],
    ).first()
    if upload is None or capture.identity_document.tenant_id != capture.tenant_id:
        raise ProviderContractError("Document capture is unavailable.")
    bucket = (
        get_object_storage_media_bucket_name()
        if upload.status == "promoted"
        else get_object_storage_temp_bucket_name()
    )
    content, _ = get_object_bytes(
        bucket_name=bucket, key=capture.storage_key, max_bytes=20 * 1024 * 1024
    )
    with Image.open(BytesIO(content)) as image:
        if image.width * image.height > 20_000_000:
            raise ProviderContractError("Document capture exceeds analysis bounds.")
        return ImageOps.exif_transpose(image).size, bucket


def collect_authenticity(*, verification, document, captures, processing_job):
    if (
        verification.policy_snapshot_json.get("document_authenticity_required")
        is not True
    ):
        return None
    outcomes = []
    for capture in captures:
        try:
            size, bucket = source_size_for_capture(capture)
            execution = execute_provider_route(
                verification=verification,
                check_type=ProviderCheckType.DOCUMENT_AUTHENTICITY,
                operation=lambda provider, timeout: normalize_authenticity(
                    invoke_selected_provider_operation(
                        provider=provider,
                        environment=(
                            verification.project.environment
                            if verification.project_id
                            else "sandbox"
                        ),
                        check_type=ProviderCheckType.DOCUMENT_AUTHENTICITY,
                        timeout_seconds=timeout,
                        operation_kwargs={
                            "verification_id": verification.public_id,
                            "document_storage_key": capture.storage_key,
                            "document_storage_bucket": bucket,
                            "source_size": list(size),
                        },
                        built_in_operation=unavailable_authenticity,
                    ),
                    source_size=size,
                ),
                request_metadata={
                    "identity_document_id": document.public_id,
                    "capture_id": capture.public_id,
                },
                processing_job=processing_job,
                finalize_exhaustion=False,
            )
            result = execution.result
            record_audit_event(
                tenant=verification.tenant,
                action="document.authenticity_checked",
                target_type="DocumentCapture",
                target_id=capture.public_id,
                metadata={
                    "provider_check_id": execution.provider_check.public_id,
                    "authenticity_version": "1",
                    "model_name": result["model_name"],
                    "model_version": result["model_version"],
                },
            )
            outcomes.append(
                {
                    "capture_id": capture.public_id,
                    "provider_check_id": execution.provider_check.public_id,
                    "result": result,
                }
            )
        except (ProcessingJobOwnershipLost, DatabaseError):
            raise
        except Exception:
            outcomes.append(
                {
                    "capture_id": capture.public_id,
                    "result": {
                        "authenticity_version": "1",
                        "status": "inconclusive",
                        "verdict": "inconclusive",
                        "confidence": None,
                        "regions": [],
                    },
                }
            )
    threshold = verification.policy_snapshot_json.get(
        "document_authenticity_min_confidence", 0.9
    )
    if (
        type(threshold) not in {int, float}
        or not math.isfinite(threshold)
        or not 0 <= threshold <= 1
    ):
        threshold = 1
    review = not outcomes or any(
        item["result"]["verdict"] != "authentic"
        or item["result"].get("confidence", 0) < threshold
        or item["result"]["regions"]
        for item in outcomes
    )
    return {
        "authenticity_version": "1",
        "requires_manual_review": review,
        "captures": outcomes,
    }
