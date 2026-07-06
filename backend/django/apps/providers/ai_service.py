import json
from urllib import request

from django.conf import settings


def _post_json(path: str, payload: dict) -> dict:
    url = f"{settings.AI_SERVICE_BASE_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings.AI_SERVICE_SHARED_TOKEN:
        headers["X-Internal-Token"] = settings.AI_SERVICE_SHARED_TOKEN
    http_request = request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    with request.urlopen(
        http_request, timeout=settings.AI_SERVICE_TIMEOUT_SECONDS
    ) as response:
        data = json.loads(response.read().decode("utf-8"))
        if "result" in data:
            normalized = dict(data["result"])
            normalized["status"] = data.get("status", normalized.get("status", ""))
            normalized["model_name"] = data.get("model_name", "")
            normalized["model_version"] = data.get("model_version", "")
            normalized["engine"] = data.get("engine", "")
            return normalized
        return data


def run_liveness_check(
    *,
    verification_id: str,
    selfie_storage_key: str,
    liveness_type: str,
    selfie_storage_bucket: str = "",
    challenge_actions: list[str] | None = None,
) -> dict:
    payload = {
        "verification_id": verification_id,
        "selfie_storage_key": selfie_storage_key,
        "liveness_type": liveness_type,
    }
    if selfie_storage_bucket:
        payload["selfie_storage_bucket"] = selfie_storage_bucket
    if challenge_actions:
        payload["challenge_actions"] = challenge_actions
    return _post_json("/v1/liveness/check", payload)


def run_face_compare(
    *,
    verification_id: str,
    selfie_storage_key: str,
    document_storage_key: str,
    threshold: float,
    selfie_storage_bucket: str = "",
    document_storage_bucket: str = "",
) -> dict:
    payload = {
        "verification_id": verification_id,
        "selfie_storage_key": selfie_storage_key,
        "document_storage_key": document_storage_key,
        "threshold": threshold,
    }
    if selfie_storage_bucket:
        payload["selfie_storage_bucket"] = selfie_storage_bucket
    if document_storage_bucket:
        payload["document_storage_bucket"] = document_storage_bucket
    return _post_json("/v1/face/compare", payload)


def run_document_ocr(
    *,
    verification_id: str,
    document_storage_key: str,
    document_type: str,
    country_code: str,
    document_storage_bucket: str = "",
) -> dict:
    payload = {
        "verification_id": verification_id,
        "document_storage_key": document_storage_key,
        "document_type": document_type,
        "country_code": country_code,
    }
    if document_storage_bucket:
        payload["document_storage_bucket"] = document_storage_bucket
    return _post_json("/v1/document/ocr", payload)


def run_document_quality(
    *,
    verification_id: str,
    document_storage_key: str,
    document_storage_bucket: str = "",
) -> dict:
    payload = {
        "verification_id": verification_id,
        "document_storage_key": document_storage_key,
    }
    if document_storage_bucket:
        payload["document_storage_bucket"] = document_storage_bucket
    return _post_json("/v1/document/quality", payload)


def run_document_classification(
    *,
    verification_id: str,
    document_storage_key: str,
    document_type: str,
    country_code: str,
    document_storage_bucket: str = "",
) -> dict:
    payload = {
        "verification_id": verification_id,
        "document_storage_key": document_storage_key,
        "document_type": document_type,
        "country_code": country_code,
    }
    if document_storage_bucket:
        payload["document_storage_bucket"] = document_storage_bucket
    return _post_json("/v1/document/classify", payload)
