# Django control plane

The Django service owns the public REST API, internal GraphQL API, persistence, and
Celery jobs. Docker is the supported copy/paste setup:

```bash
cp .env.example .env
docker compose up --build -d postgres redis ai-service django celery-worker celery-worker-ai celery-worker-retention celery-worker-webhooks celery-worker-notifications celery-beat
docker compose exec django python manage.py migrate
curl http://localhost:8000/api/v1/health
```

Run its checks from the repository root:

```bash
docker compose run --rm -e DJANGO_SETTINGS_MODULE=config.settings.testing django python manage.py test
docker compose run --rm django ruff check .
docker compose run --rm django black --check .
docker compose run --rm django mypy backend
```

The application listens on `8000`; PostgreSQL and Redis are reached inside Compose at
`postgres:5432` and `redis:6379`. Configuration comes from [`.env.example`](../../.env.example).
The required groups are Django (`DJANGO_*`, `JWT_SIGNING_KEY`), database (`POSTGRES_*`),
queues (`REDIS_URL`, `CELERY_*`), AI (`AI_SERVICE_*`), storage (`OBJECT_STORAGE_*`),
encryption (`APPLICATION_ENCRYPTION_*`), and notifications (`EMAIL_*`, `NOTIFICATION_*`).
Production settings reject development secrets and incomplete configuration.
