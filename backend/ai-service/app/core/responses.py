from app.schemas.processing import AIResultResponse, HealthResponse
from app.settings import get_settings


def service_metadata() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        mode=settings.service_mode,
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
