import asyncio

from app.main import FaceCompareRequest, LivenessCheckRequest, face_compare, healthcheck, liveness_check


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
