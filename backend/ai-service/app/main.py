from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.settings import get_settings


settings = get_settings()
app = FastAPI(title="IdentityCore AI Service", version=settings.service_version)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mode: str


class FaceCompareRequest(BaseModel):
    verification_id: str
    selfie_storage_key: str
    document_storage_key: str
    threshold: float = Field(ge=0.0, le=1.0)


class LivenessCheckRequest(BaseModel):
    verification_id: str
    selfie_storage_key: str
    liveness_type: str


class DocumentOCRRequest(BaseModel):
    verification_id: str
    document_storage_key: str
    document_type: str
    country_code: str = Field(min_length=2, max_length=2)


class DocumentQualityRequest(BaseModel):
    verification_id: str
    document_storage_key: str


class AIResultResponse(BaseModel):
    status: str
    engine: str
    model_name: str
    model_version: str
    result: dict[str, Any]


def _service_metadata() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        mode=settings.service_mode,
    )


def _enforce_internal_token(
    x_internal_token: Annotated[str | None, Header()] = None,
) -> None:
    if settings.shared_token and x_internal_token != settings.shared_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized internal AI service request.",
        )


def _face_compare_result(payload: FaceCompareRequest) -> AIResultResponse:
    matched = (
        "mismatch" not in payload.selfie_storage_key
        and "mismatch" not in payload.document_storage_key
    )
    match_score = 0.96 if matched else 0.42
    return AIResultResponse(
        status="completed",
        engine=settings.service_mode,
        model_name="mock-face-match",
        model_version="v1",
        result={
            "match_score": match_score,
            "confidence_level": "high" if matched else "medium",
            "matched": matched,
            "threshold_used": payload.threshold,
        },
    )


def _liveness_result(payload: LivenessCheckRequest) -> AIResultResponse:
    passed = "spoof" not in payload.selfie_storage_key
    score = 0.94 if passed else 0.23
    return AIResultResponse(
        status="completed",
        engine=settings.service_mode,
        model_name="mock-liveness",
        model_version="v1",
        result={
            "score": score,
            "confidence_level": "high" if passed else "medium",
            "passed": passed,
            "liveness_type": payload.liveness_type,
        },
    )


def _document_ocr_result(payload: DocumentOCRRequest) -> AIResultResponse:
    return AIResultResponse(
        status="completed",
        engine=settings.service_mode,
        model_name="mock-ocr",
        model_version="v1",
        result={
            "confidence_score": 0.91,
            "extracted_fields": {
                "full_name": "Kwame Mensah",
                "date_of_birth": "1998-01-01",
                "document_number": f"hash:{payload.document_type}:{payload.country_code}",
            },
        },
    )


def _document_quality_result(payload: DocumentQualityRequest) -> AIResultResponse:
    issues = ["blur_detected"] if "blur" in payload.document_storage_key else []
    score = 0.42 if issues else 0.88
    return AIResultResponse(
        status="completed",
        engine=settings.service_mode,
        model_name="mock-document-quality",
        model_version="v1",
        result={
            "quality_score": score,
            "issues": issues,
        },
    )


@app.get("/v1/health", response_model=HealthResponse)
async def healthcheck() -> dict[str, str]:
    return _service_metadata().model_dump()


@app.get(
    "/v1/ready",
    response_model=HealthResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def readiness() -> dict[str, str]:
    return _service_metadata().model_dump()


@app.post(
    "/v1/face/compare",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def face_compare(payload: FaceCompareRequest) -> dict[str, Any]:
    return _face_compare_result(payload).model_dump()


@app.post(
    "/v1/liveness/check",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def liveness_check(payload: LivenessCheckRequest) -> dict[str, Any]:
    return _liveness_result(payload).model_dump()


@app.post(
    "/v1/document/ocr",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def document_ocr(payload: DocumentOCRRequest) -> dict[str, Any]:
    return _document_ocr_result(payload).model_dump()


@app.post(
    "/v1/document/quality",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def document_quality(payload: DocumentQualityRequest) -> dict[str, Any]:
    return _document_quality_result(payload).model_dump()
