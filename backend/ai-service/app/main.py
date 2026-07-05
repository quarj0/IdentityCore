from pydantic import BaseModel
from fastapi import FastAPI


app = FastAPI(title="IdentityCore AI Service")


@app.get("/v1/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "ai-service"}


class FaceCompareRequest(BaseModel):
    verification_id: str
    selfie_storage_key: str
    document_storage_key: str
    threshold: float


class LivenessCheckRequest(BaseModel):
    verification_id: str
    selfie_storage_key: str
    liveness_type: str


@app.post("/v1/face/compare")
async def face_compare(payload: FaceCompareRequest) -> dict[str, str | float | bool]:
    matched = "mismatch" not in payload.selfie_storage_key and "mismatch" not in payload.document_storage_key
    match_score = 0.96 if matched else 0.42
    return {
        "status": "completed",
        "match_score": match_score,
        "confidence_level": "high" if matched else "medium",
        "matched": matched,
        "threshold_used": payload.threshold,
        "model_name": "mock-face-match",
        "model_version": "v1",
    }


@app.post("/v1/liveness/check")
async def liveness_check(payload: LivenessCheckRequest) -> dict[str, str | float | bool]:
    passed = "spoof" not in payload.selfie_storage_key
    score = 0.94 if passed else 0.23
    return {
        "status": "completed",
        "score": score,
        "confidence_level": "high" if passed else "medium",
        "passed": passed,
        "model_name": "mock-liveness",
        "model_version": "v1",
    }
