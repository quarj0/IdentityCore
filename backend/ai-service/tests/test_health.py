import asyncio

from app.main import (
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    LivenessCheckRequest,
    document_ocr,
    document_quality,
    face_compare,
    healthcheck,
    liveness_check,
)


def test_healthcheck():
    response = asyncio.run(healthcheck())

    assert response == {"status": "ok", "service": "ai-service"}


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
    assert response["matched"] is True


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
    assert response["passed"] is False


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
    assert "full_name" in response["extracted_fields"]


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
    assert response["issues"] == ["blur_detected"]
