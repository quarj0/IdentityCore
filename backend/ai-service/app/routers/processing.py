from typing import Any

from fastapi import APIRouter, Depends

from app.core.auth import enforce_internal_token
from app.core.responses import wrap_result
from app.schemas.processing import (
    AIResultResponse,
    DocumentClassificationRequest,
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    LivenessCheckRequest,
)
from app.services.processing import (
    process_document_classification,
    process_document_ocr,
    process_document_quality,
    process_face_compare,
    process_liveness,
)


router = APIRouter()


@router.post(
    "/v1/face/compare",
    response_model=AIResultResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def face_compare(payload: FaceCompareRequest) -> dict[str, Any]:
    return wrap_result(process_face_compare(payload))


@router.post(
    "/v1/liveness/check",
    response_model=AIResultResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def liveness_check(payload: LivenessCheckRequest) -> dict[str, Any]:
    return wrap_result(process_liveness(payload))


@router.post(
    "/v1/document/ocr",
    response_model=AIResultResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def document_ocr(payload: DocumentOCRRequest) -> dict[str, Any]:
    return wrap_result(process_document_ocr(payload))


@router.post(
    "/v1/document/quality",
    response_model=AIResultResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def document_quality(payload: DocumentQualityRequest) -> dict[str, Any]:
    return wrap_result(process_document_quality(payload))


@router.post(
    "/v1/document/classify",
    response_model=AIResultResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def document_classify(payload: DocumentClassificationRequest) -> dict[str, Any]:
    return wrap_result(process_document_classification(payload))
