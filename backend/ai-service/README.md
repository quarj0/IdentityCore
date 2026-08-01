# Internal AI service

FastAPI performs document quality/classification/OCR and biometric checks. It is an
internal service, not a browser-facing API, and requires `X-Internal-Token`.

```bash
cp .env.example .env
docker compose up --build -d ai-service
curl -H "X-Internal-Token: $(sed -n 's/^AI_SERVICE_SHARED_TOKEN=//p' .env)" http://localhost:8001/v1/ready
docker compose run --rm ai-service pytest
```

The service listens on `8001`. `AI_SERVICE_SHARED_TOKEN`, `AI_SERVICE_MODE`, and
`AI_MODEL_ROOT` are required runtime settings. `INSIGHTFACE_MODEL_NAME`,
`INSIGHTFACE_ALLOW_DOWNLOAD`, and `PADDLE_OCR_ALLOW_DOWNLOAD` control model loading.
Production images should preload models; bootstrap the named Compose volume explicitly
when downloads are intended:

```bash
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
```

Storage and encryption variables are shared with Django and documented in
[`.env.example`](../../.env.example). Never expose this port publicly or log media,
extracted identity attributes, embeddings, or the shared token.
