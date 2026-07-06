from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mode: str


class ReadinessResponse(HealthResponse):
    ready: bool
    checks: dict[str, str]
    missing_requirements: list[str] = Field(default_factory=list)


class FaceCompareRequest(BaseModel):
    verification_id: str
    selfie_storage_key: str
    document_storage_key: str
    selfie_storage_bucket: str | None = None
    document_storage_bucket: str | None = None
    threshold: float = Field(ge=0.0, le=1.0)


class LivenessCheckRequest(BaseModel):
    verification_id: str
    selfie_storage_key: str
    selfie_storage_bucket: str | None = None
    liveness_type: str
    challenge_actions: list[str] = Field(default_factory=list)


class DocumentOCRRequest(BaseModel):
    verification_id: str
    document_storage_key: str
    document_storage_bucket: str | None = None
    document_type: str
    country_code: str = Field(default="", max_length=2)


class DocumentQualityRequest(BaseModel):
    verification_id: str
    document_storage_key: str
    document_storage_bucket: str | None = None


class DocumentClassificationRequest(BaseModel):
    verification_id: str
    document_storage_key: str
    document_storage_bucket: str | None = None
    document_type: str
    country_code: str = Field(default="", max_length=2)


class AIResultResponse(BaseModel):
    status: str
    engine: str
    model_name: str
    model_version: str
    result: dict[str, Any]
    fallback_reason: str | None = None
