from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.pipeline import (
    build_mock_document_ocr,
    build_mock_document_quality,
    build_mock_face_compare,
    build_mock_liveness,
    run_document_ocr_pipeline,
    run_document_quality_pipeline,
    run_face_compare_pipeline,
    run_liveness_pipeline,
    run_with_mode,
)
from app.runtime import configure_runtime_environment
from app.settings import get_settings


settings = get_settings()
configure_runtime_environment(settings)
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
    fallback_reason: str | None = None


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


def _wrap_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in payload.items() if key not in {"status", "engine", "fallback_reason"}}
    return AIResultResponse(
        status=payload["status"],
        engine=payload["engine"],
        model_name=result.pop("model_name"),
        model_version=result.pop("model_version"),
        result=result,
        fallback_reason=payload.get("fallback_reason"),
    ).model_dump()


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
    return _wrap_result(
        run_with_mode(
            real_callable=lambda: run_face_compare_pipeline(
                selfie_storage_key=payload.selfie_storage_key,
                document_storage_key=payload.document_storage_key,
                threshold=payload.threshold,
            ),
            mock_callable=build_mock_face_compare,
            mock_args=(
                payload.selfie_storage_key,
                payload.document_storage_key,
                payload.threshold,
            ),
        )
    )


@app.post(
    "/v1/liveness/check",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def liveness_check(payload: LivenessCheckRequest) -> dict[str, Any]:
    return _wrap_result(
        run_with_mode(
            real_callable=lambda: run_liveness_pipeline(
                storage_key=payload.selfie_storage_key,
                liveness_type=payload.liveness_type,
            ),
            mock_callable=build_mock_liveness,
            mock_args=(payload.selfie_storage_key, payload.liveness_type),
        )
    )


@app.post(
    "/v1/document/ocr",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def document_ocr(payload: DocumentOCRRequest) -> dict[str, Any]:
    return _wrap_result(
        run_with_mode(
            real_callable=lambda: run_document_ocr_pipeline(
                storage_key=payload.document_storage_key,
                document_type=payload.document_type,
                country_code=payload.country_code,
            ),
            mock_callable=build_mock_document_ocr,
            mock_args=(
                payload.document_storage_key,
                payload.document_type,
                payload.country_code,
            ),
        )
    )


@app.post(
    "/v1/document/quality",
    response_model=AIResultResponse,
    dependencies=[Depends(_enforce_internal_token)],
)
async def document_quality(payload: DocumentQualityRequest) -> dict[str, Any]:
    return _wrap_result(
        run_with_mode(
            real_callable=lambda: run_document_quality_pipeline(
                storage_key=payload.document_storage_key,
            ),
            mock_callable=build_mock_document_quality,
            mock_args=(payload.document_storage_key,),
        )
    )
