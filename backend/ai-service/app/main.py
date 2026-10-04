from app.core.safe_logging import install_safe_logging

# Install before importing processing modules so initialization failures and
# exception paths cannot emit raw evidence or credentials.
install_safe_logging()

from fastapi import FastAPI  # noqa: E402

from app.core.auth import (
    enforce_internal_token as _enforce_internal_token,
)  # noqa: E402
from app.routers.health import (
    healthcheck,
    readiness,
    router as health_router,
)  # noqa: E402
from app.routers.processing import (  # noqa: E402
    document_classify,
    document_ocr,
    document_quality,
    face_compare,
    liveness_check,
    router as processing_router,
)
from app.runtime import configure_runtime_environment  # noqa: E402
from app.schemas.processing import (  # noqa: E402
    AIResultResponse,
    DocumentClassificationRequest,
    DocumentOCRRequest,
    DocumentQualityRequest,
    FaceCompareRequest,
    HealthResponse,
    LivenessCheckRequest,
    ReadinessResponse,
)
from app.settings import get_settings  # noqa: E402

settings = get_settings()
configure_runtime_environment(settings)

app = FastAPI(title="IdentityCore AI Service", version=settings.service_version)
from shared import observability as telemetry

telemetry.configure("identitycore-ai")


@app.middleware("http")
async def observe_request(request, call_next):
    trusted = (
        bool(settings.shared_token)
        and request.headers.get("X-Internal-Token") == settings.shared_token
    )
    token = telemetry.ENVIRONMENT.set(
        telemetry.environment(
            request.headers.get("X-IdentityCore-Environment") if trusted else "unknown"
        )
    )
    try:
        with telemetry.operation(
            "ai", "request", context=telemetry.extract(request.headers)
        ) as span:
            response = await call_next(request)
            telemetry.record_response("ai", response.status_code >= 500)
            if response.status_code >= 500:
                span.set_status(telemetry.Status(telemetry.StatusCode.ERROR))
            return response
    finally:
        telemetry.ENVIRONMENT.reset(token)


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
