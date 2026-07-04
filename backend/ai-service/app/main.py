from fastapi import FastAPI


app = FastAPI(title="IdentityCore AI Service")


@app.get("/v1/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "ai-service"}
