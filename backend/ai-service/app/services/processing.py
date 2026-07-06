from app.pipeline import (
    build_mock_document_classification,
    build_mock_document_ocr,
    build_mock_document_quality,
    build_mock_face_compare,
    build_mock_liveness,
    run_document_classification_pipeline,
    run_document_ocr_pipeline,
    run_document_quality_pipeline,
    run_face_compare_pipeline,
    run_liveness_pipeline,
    run_with_mode,
)
from app.schemas.processing import (
    DocumentClassificationRequest,
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    LivenessCheckRequest,
)


def process_face_compare(payload: FaceCompareRequest) -> dict:
    return run_with_mode(
        real_callable=lambda: run_face_compare_pipeline(
            selfie_storage_key=payload.selfie_storage_key,
            document_storage_key=payload.document_storage_key,
            threshold=payload.threshold,
            selfie_bucket_name=payload.selfie_storage_bucket,
            document_bucket_name=payload.document_storage_bucket,
        ),
        mock_callable=build_mock_face_compare,
        mock_args=(
            payload.selfie_storage_key,
            payload.document_storage_key,
            payload.threshold,
        ),
    )


def process_liveness(payload: LivenessCheckRequest) -> dict:
    return run_with_mode(
        real_callable=lambda: run_liveness_pipeline(
            storage_key=payload.selfie_storage_key,
            liveness_type=payload.liveness_type,
            challenge_actions=payload.challenge_actions,
            bucket_name=payload.selfie_storage_bucket,
        ),
        mock_callable=build_mock_liveness,
        mock_args=(
            payload.selfie_storage_key,
            payload.liveness_type,
            payload.challenge_actions,
        ),
    )


def process_document_ocr(payload: DocumentOCRRequest) -> dict:
    return run_with_mode(
        real_callable=lambda: run_document_ocr_pipeline(
            storage_key=payload.document_storage_key,
            document_type=payload.document_type,
            country_code=payload.country_code,
            bucket_name=payload.document_storage_bucket,
        ),
        mock_callable=build_mock_document_ocr,
        mock_args=(
            payload.document_storage_key,
            payload.document_type,
            payload.country_code,
        ),
    )


def process_document_quality(payload: DocumentQualityRequest) -> dict:
    return run_with_mode(
        real_callable=lambda: run_document_quality_pipeline(
            storage_key=payload.document_storage_key,
            bucket_name=payload.document_storage_bucket,
        ),
        mock_callable=build_mock_document_quality,
        mock_args=(payload.document_storage_key,),
    )


def process_document_classification(payload: DocumentClassificationRequest) -> dict:
    return run_with_mode(
        real_callable=lambda: run_document_classification_pipeline(
            storage_key=payload.document_storage_key,
            expected_document_type=payload.document_type,
            country_code=payload.country_code,
            bucket_name=payload.document_storage_bucket,
        ),
        mock_callable=build_mock_document_classification,
        mock_args=(
            payload.document_storage_key,
            payload.document_type,
            payload.country_code,
        ),
    )
