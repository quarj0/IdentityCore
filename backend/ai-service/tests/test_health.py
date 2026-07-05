import asyncio

import cv2
import numpy as np
import pytest
from fastapi import HTTPException

from app.main import (
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    LivenessCheckRequest,
    _enforce_internal_token,
    document_ocr,
    document_quality,
    face_compare,
    healthcheck,
    liveness_check,
)
from app.pipeline import run_document_quality_pipeline
from app.settings import get_settings


def test_healthcheck():
    response = asyncio.run(healthcheck())

    assert response["status"] == "ok"
    assert response["service"] == "ai-service"
    assert response["mode"] == "mock"


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
