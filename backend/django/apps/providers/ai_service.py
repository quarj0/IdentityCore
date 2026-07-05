import json
from urllib import request

from django.conf import settings


def _post_json(path: str, payload: dict) -> dict:
    url = f"{settings.AI_SERVICE_BASE_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=settings.AI_SERVICE_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def run_liveness_check(*, verification_id: str, selfie_storage_key: str, liveness_type: str) -> dict:
    return _post_json(
        "/v1/liveness/check",
        {
            "verification_id": verification_id,
            "selfie_storage_key": selfie_storage_key,
            "liveness_type": liveness_type,
        },
    )


def run_face_compare(
    *,
    verification_id: str,
    selfie_storage_key: str,
    document_storage_key: str,
    threshold: float,
) -> dict:
    return _post_json(
        "/v1/face/compare",
        {
            "verification_id": verification_id,
            "selfie_storage_key": selfie_storage_key,
            "document_storage_key": document_storage_key,
            "threshold": threshold,
        },
    )


def run_document_ocr(
    *,
    verification_id: str,
    document_storage_key: str,
    document_type: str,
    country_code: str,
) -> dict:
    return _post_json(
        "/v1/document/ocr",
        {
            "verification_id": verification_id,
            "document_storage_key": document_storage_key,
            "document_type": document_type,
            "country_code": country_code,
        },
    )


def run_document_quality(*, verification_id: str, document_storage_key: str) -> dict:
    return _post_json(
        "/v1/document/quality",
        {
            "verification_id": verification_id,
            "document_storage_key": document_storage_key,
        },
    )
