import json
import socket
from urllib import error, request

from django.conf import settings


AI_SERVICE_UNAVAILABLE_MESSAGE = (
    "The verification service is temporarily unavailable. Please try again shortly."
)


class AIServiceUnavailable(RuntimeError):
    def __init__(
        self,
        message: str = AI_SERVICE_UNAVAILABLE_MESSAGE,
        *,
        error_code: str = "provider_unavailable",
        provider_check_status: str = "failed",
        reason: str = "",
    ):
        super().__init__(message)
        self.error_code = error_code
        self.provider_check_status = provider_check_status
        self.reason = reason


def _safe_error_reason(response_body: bytes) -> str:
    try:
        payload = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message") or payload.get("error")
        if isinstance(detail, str):
            return detail
    return ""


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
    try:
        with request.urlopen(
            http_request, timeout=settings.AI_SERVICE_TIMEOUT_SECONDS
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        reason = _safe_error_reason(exc.read())
        raise AIServiceUnavailable(
            error_code=f"provider_http_{exc.code}",
            reason=reason or f"AI service returned HTTP {exc.code}.",
        ) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise AIServiceUnavailable(
            error_code="provider_timeout",
            provider_check_status="timeout",
            reason="AI service request timed out.",
        ) from exc
    except error.URLError as exc:
        raise AIServiceUnavailable(
            reason=f"AI service network error: {exc.reason}",
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AIServiceUnavailable(
            error_code="provider_invalid_response",
            reason="AI service returned an invalid response.",
        ) from exc

    if not isinstance(data, dict):
        raise AIServiceUnavailable(
            error_code="provider_invalid_response",
            reason="AI service returned an unexpected response shape.",
        )
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
