# IdentityCore backend

The backend workspace contains the Django control plane and the internal FastAPI AI
service. From the repository root, copy the development configuration and start the
complete backend stack:

```bash
cp .env.example .env
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
