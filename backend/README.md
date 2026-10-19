# IdentityCore backend

The backend workspace contains the Django control plane and the internal FastAPI AI
service. Run these commands from the repository root. For the real-mode stack,
copy the development configuration, then configure its storage endpoints/credentials,
internal service token and other required settings before starting services:

```bash
cp .env.example .env
```

Real mode requires provisioned model assets; runtime downloads are disabled. Fetch
the pinned PAD candidate and bootstrap the named model volume before starting the
workers (see the [AI model guide](ai-service/README.md) for approval and checksum
requirements). These downloads need network access and disk space; they do not
establish biometric accuracy or production approval:

```bash
docker compose --profile model-bootstrap run --rm --build --entrypoint python \
  ai-model-bootstrap /app/scripts/fetch_pad_model.py \
  --model-root /opt/identitycore/models
docker compose --profile model-bootstrap run --rm ai-model-bootstrap
# Review the candidate manifest and configure AI_MODEL_MANIFEST_SHA256 in .env.
# Follow docs/operations/ai-models.md; do not trust a digest from a mutable volume automatically.
docker compose up --build -d
curl http://localhost:8000/api/v1/health
curl -H "X-Internal-Token: $(sed -n 's/^AI_SERVICE_SHARED_TOKEN=//p' .env)" http://localhost:8001/v1/ready
```

PostgreSQL is exposed on `5433`, Redis on `6379`, Django on `8000`, and the AI
service on `8001`. The Celery workers and scheduler have no host ports. See
[`django/README.md`](django/README.md) and [`ai-service/README.md`](ai-service/README.md)
for service-specific commands and configuration. The root [`.env.example`](../.env.example)
is the authoritative variable list; its values are for local development only.

Run all backend tests with `make test` and static checks with `make lint`.
