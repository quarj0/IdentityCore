import asyncio

import pytest
from botocore.exceptions import ClientError

pytest.importorskip("fastapi")

from fastapi import HTTPException

from app.main import (
    DocumentClassificationRequest,
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    LivenessCheckRequest,
    _enforce_internal_token,
    document_classify,
    document_ocr,
    document_quality,
    face_compare,
    healthcheck,
    liveness_check,
    readiness,
)
from app.pipeline import run_document_quality_pipeline
from app.settings import Settings, get_settings


def test_healthcheck():
    response = asyncio.run(healthcheck())

    assert response["status"] == "ok"
    assert response["service"] == "ai-service"
    assert response["mode"] == "mock"


def test_readiness_is_ok_in_mock_mode():
    response = asyncio.run(readiness())

    assert response.status_code == 200


def test_face_compare_returns_completed_match_result():
    response = asyncio.run(
        face_compare(
            FaceCompareRequest(
                verification_id="ver_01TEST",
                selfie_storage_key="uploads/selfies/sel_good",
                document_storage_key="uploads/documents/doc_good",
                threshold=0.85,
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["matched"] is True


def test_liveness_check_returns_failed_for_spoof_key():
    response = asyncio.run(
        liveness_check(
            LivenessCheckRequest(
                verification_id="ver_01TEST",
                selfie_storage_key="uploads/selfies/spoof_case",
                liveness_type="passive",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["passed"] is False


def test_active_liveness_returns_challenge_metadata():
    response = asyncio.run(
        liveness_check(
            LivenessCheckRequest(
                verification_id="ver_01TEST",
                selfie_storage_key="uploads/selfies/sel_good",
                liveness_type="active",
                challenge_actions=["turn_left", "turn_right"],
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["challenge_passed"] is True


def test_document_ocr_returns_extracted_fields():
    response = asyncio.run(
        document_ocr(
            DocumentOCRRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/doc_good",
                document_type="national_id",
                country_code="GH",
            )
        )
    )

    assert response["status"] == "completed"
    assert "full_name" in response["result"]["extracted_fields"]


def test_document_ocr_returns_manual_review_when_media_is_missing(monkeypatch):
    missing_object_error = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )

    def raise_missing_object(*args, **kwargs):
        raise missing_object_error

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", raise_missing_object)

    response = asyncio.run(
        document_ocr(
            DocumentOCRRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/missing.jpg",
                document_type="national_id",
                country_code="GH",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["confidence_score"] == 0.0
    assert response["result"]["requires_manual_review"] is True
    assert response["result"]["manual_review"]["required"] is True
    assert "document_media_missing" in response["result"]["issues"]


def test_document_quality_flags_blurry_capture():
    response = asyncio.run(
        document_quality(
            DocumentQualityRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/doc_blur_case",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["issues"] == ["blur_detected"]


def test_document_quality_returns_review_signal_when_media_is_missing(monkeypatch):
    missing_object_error = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )

    def raise_missing_object(*args, **kwargs):
        raise missing_object_error

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", raise_missing_object)

    response = asyncio.run(
        document_quality(
            DocumentQualityRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/missing.jpg",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["issues"] == ["document_media_missing"]
    assert response["result"]["quality_score"] == 0.0


def test_document_quality_falls_back_to_alternate_bucket(monkeypatch):
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    image = np.full((120, 120, 3), 180, dtype=np.uint8)
    cv2.putText(
        image,
        "ID",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    success, encoded = cv2.imencode(".jpg", image)
    assert success is True

    seen_buckets: list[str | None] = []

    def fetch_from_media(storage_key, *, bucket_name=None):
        seen_buckets.append(bucket_name)
        if bucket_name == "identitycore-media":
            return encoded.tobytes()
        raise ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "GetObject",
        )

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", fetch_from_media)
    monkeypatch.setenv("OBJECT_STORAGE_MEDIA_BUCKET", "identitycore-media")
    monkeypatch.setenv("OBJECT_STORAGE_TEMP_BUCKET", "identitycore-temp")
    get_settings.cache_clear()

    try:
        response = asyncio.run(
            document_quality(
                DocumentQualityRequest(
                    verification_id="ver_01TEST",
                    document_storage_key="uploads/documents/fallback.jpg",
                )
            )
        )
    finally:
        monkeypatch.delenv("OBJECT_STORAGE_MEDIA_BUCKET", raising=False)
        monkeypatch.delenv("OBJECT_STORAGE_TEMP_BUCKET", raising=False)
        get_settings.cache_clear()

    assert response["status"] == "completed"
    assert "identitycore-media" in seen_buckets
    assert response["result"]["model_name"] == "opencv-quality"


def test_document_classification_returns_predicted_type():
    response = asyncio.run(
        document_classify(
            DocumentClassificationRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/national_id_front",
                document_type="national_id",
                country_code="GH",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["predicted_document_type"] == "national_id"
    assert response["result"]["classification_status"] == "recognized"
    assert response["result"]["workflow_action"] == "continue"
    assert response["result"]["manual_review"]["required"] is False


def test_document_classification_returns_manual_review_when_media_is_missing(
    monkeypatch,
):
    missing_object_error = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )

    def raise_missing_object(*args, **kwargs):
        raise missing_object_error

    monkeypatch.setattr("app.pipeline.fetch_object_bytes", raise_missing_object)

    response = asyncio.run(
        document_classify(
            DocumentClassificationRequest(
                verification_id="ver_01TEST",
                document_storage_key="uploads/documents/missing.jpg",
                document_type="national_id",
                country_code="GH",
            )
        )
    )

    assert response["status"] == "completed"
    assert response["result"]["classification_status"] == "unknown"
    assert response["result"]["workflow_action"] == "continue_with_review"
    assert response["result"]["requires_manual_review"] is True
    assert response["result"]["manual_review"]["required"] is True
    assert "document_media_missing" in response["result"]["issues"]


def test_internal_token_is_enforced_when_configured(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_SHARED_TOKEN", "internal-secret")
    get_settings.cache_clear()

    from app import main as main_module

    main_module.settings = get_settings()
    with pytest.raises(HTTPException) as exc:
        _enforce_internal_token("wrong-token")

    _enforce_internal_token("internal-secret")

    assert exc.value.status_code == 401

    monkeypatch.delenv("AI_SERVICE_SHARED_TOKEN", raising=False)
    get_settings.cache_clear()
    main_module.settings = get_settings()


def test_real_document_quality_pipeline_detects_blur(monkeypatch):
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    image = np.full((320, 480, 3), 255, dtype=np.uint8)
    cv2.putText(
        image,
        "IDENTITY",
        (40, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        2.0,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    blurred = cv2.GaussianBlur(image, (31, 31), 0)
    success, encoded = cv2.imencode(".jpg", blurred)
    assert success is True

    monkeypatch.setattr(
        "app.pipeline.fetch_object_bytes",
        lambda storage_key: encoded.tobytes(),
    )

    result = run_document_quality_pipeline("uploads/documents/doc_blurred.jpg")

    assert result["model_name"] == "opencv-quality"
    assert "blur_detected" in result["issues"]


def test_local_service_mode_alias_normalizes_to_mock():
    settings = Settings(AI_SERVICE_MODE="local")

    assert settings.service_mode == "mock"


def test_real_mode_requires_storage_and_models(tmp_path):
    settings = Settings(
        AI_SERVICE_MODE="real",
        OBJECT_STORAGE_MEDIA_BUCKET="identitycore-media",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        INSIGHTFACE_ALLOW_DOWNLOAD=False,
        PADDLE_OCR_ALLOW_DOWNLOAD=False,
        AI_MODEL_ROOT=tmp_path,
    )

    missing = settings.real_inference_missing_requirements()

    assert any(item.startswith("models.insightface:") for item in missing)
    assert any(item.startswith("models.paddleocr.det:") for item in missing)


def test_real_mode_accepts_r2_storage_aliases():
    settings = Settings(
        AI_SERVICE_MODE="real",
        R2_MEDIA_BUCKET="identitycore-media",
        R2_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        R2_ACCESS_KEY_ID="key",
        R2_SECRET_ACCESS_KEY="secret",
        INSIGHTFACE_ALLOW_DOWNLOAD=True,
        PADDLE_OCR_ALLOW_DOWNLOAD=True,
    )

    assert settings.real_inference_missing_requirements() == []


def test_hybrid_mode_is_degraded_but_ready_when_real_requirements_are_missing(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_MODE", "hybrid")
    monkeypatch.setenv("OBJECT_STORAGE_MEDIA_BUCKET", "")
    monkeypatch.setenv("OBJECT_STORAGE_BUCKET", "")
    monkeypatch.setenv("OBJECT_STORAGE_ENDPOINT_URL", "")
    monkeypatch.setenv("OBJECT_STORAGE_ACCESS_KEY_ID", "")
    monkeypatch.setenv("OBJECT_STORAGE_SECRET_ACCESS_KEY", "")
    monkeypatch.setenv("INSIGHTFACE_ALLOW_DOWNLOAD", "0")
    monkeypatch.setenv("PADDLE_OCR_ALLOW_DOWNLOAD", "0")
    get_settings.cache_clear()

    response = asyncio.run(readiness())
    payload = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "\"status\":\"degraded\"" in payload
    assert "\"ready\":true" in payload

    monkeypatch.delenv("AI_SERVICE_MODE", raising=False)
    monkeypatch.delenv("INSIGHTFACE_ALLOW_DOWNLOAD", raising=False)
    monkeypatch.delenv("PADDLE_OCR_ALLOW_DOWNLOAD", raising=False)
    get_settings.cache_clear()
