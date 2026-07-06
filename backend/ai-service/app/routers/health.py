from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.auth import enforce_internal_token
from app.core.responses import service_metadata, service_readiness
from app.schemas.processing import HealthResponse, ReadinessResponse


router = APIRouter()


@router.get("/v1/health", response_model=HealthResponse)
async def healthcheck() -> dict[str, str]:
    return service_metadata().model_dump()


@router.get(
    "/v1/ready",
    response_model=ReadinessResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def readiness():
    readiness_payload = service_readiness()
    status_code = status.HTTP_200_OK if readiness_payload.ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content=readiness_payload.model_dump(),
    )
