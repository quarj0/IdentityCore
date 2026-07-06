from app.schemas.processing import AIResultResponse, HealthResponse, ReadinessResponse
from app.settings import get_settings


def service_metadata() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        mode=settings.service_mode,
    )


def service_readiness() -> ReadinessResponse:
    settings = get_settings()
    missing_requirements = settings.real_inference_missing_requirements()

    if settings.service_mode == "mock":
        return ReadinessResponse(
            status="ok",
            service=settings.service_name,
            version=settings.service_version,
            mode=settings.service_mode,
            ready=True,
            checks={"runtime_mode": "mock", "real_inference": "not_required"},
            missing_requirements=[],
        )

    real_status = "ready" if not missing_requirements else "missing_requirements"
    ready = settings.service_mode == "hybrid" or not missing_requirements
    status = "ok" if ready else "error"
    if settings.service_mode == "hybrid" and missing_requirements:
        status = "degraded"

    return ReadinessResponse(
        status=status,
        service=settings.service_name,
        version=settings.service_version,
        mode=settings.service_mode,
        ready=ready,
        checks={
            "runtime_mode": settings.service_mode,
            "real_inference": real_status,
            "mock_fallback": "enabled" if settings.mock_fallback_enabled else "disabled",
        },
        missing_requirements=missing_requirements,
    )


def wrap_result(payload: dict) -> dict:
    result = {
        key: value
        for key, value in payload.items()
        if key not in {"status", "engine", "fallback_reason"}
    }
    return AIResultResponse(
        status=payload["status"],
        engine=payload["engine"],
        model_name=result.pop("model_name"),
        model_version=result.pop("model_version"),
        result=result,
        fallback_reason=payload.get("fallback_reason"),
    ).model_dump()
