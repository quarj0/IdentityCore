from fastapi import APIRouter, Depends

from app.core.auth import enforce_internal_token
from app.core.responses import service_metadata
from app.schemas.processing import HealthResponse


router = APIRouter()


@router.get("/v1/health", response_model=HealthResponse)
async def healthcheck() -> dict[str, str]:
    return service_metadata().model_dump()


@router.get(
    "/v1/ready",
    response_model=HealthResponse,
    dependencies=[Depends(enforce_internal_token)],
)
async def readiness() -> dict[str, str]:
    return service_metadata().model_dump()
