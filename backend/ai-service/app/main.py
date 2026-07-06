from fastapi import FastAPI

from app.core.auth import enforce_internal_token as _enforce_internal_token
from app.routers.health import healthcheck, readiness, router as health_router
from app.routers.processing import (
    document_classify,
    document_ocr,
    document_quality,
    face_compare,
    liveness_check,
    router as processing_router,
)
from app.runtime import configure_runtime_environment
from app.schemas.processing import (
    AIResultResponse,
    DocumentClassificationRequest,
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    HealthResponse,
    LivenessCheckRequest,
    ReadinessResponse,
)
from app.settings import get_settings


settings = get_settings()
configure_runtime_environment(settings)

app = FastAPI(title="IdentityCore AI Service", version=settings.service_version)
app.include_router(health_router)
app.include_router(processing_router)

__all__ = [
    "AIResultResponse",
    "DocumentClassificationRequest",
    "DocumentOCRRequest",
    "DocumentQualityRequest",
    "FaceCompareRequest",
    "HealthResponse",
    "LivenessCheckRequest",
    "ReadinessResponse",
    "_enforce_internal_token",
    "app",
    "document_ocr",
    "document_classify",
    "document_quality",
    "face_compare",
    "healthcheck",
    "liveness_check",
    "readiness",
]
