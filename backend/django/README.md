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

## Multi-factor authentication

Platform administrators require TOTP MFA when `security.admin_mfa_required` is enabled
(the default). Organizations can require MFA for selected tenant roles by setting
`privileged_mfa_roles` in their encrypted organization settings to an array of exact
role names. Password login then returns HTTP 202 with a five-minute `mfa_token` rather
than session credentials.

Use `POST /api/v1/auth/mfa/enroll` and `/mfa/enroll/confirm` for first-time setup, then
`POST /api/v1/auth/mfa/challenge` on later logins. Enrollment confirmation returns ten
single-use recovery codes; they are shown once and stored only as hashes. An
authenticated user can use `POST /api/v1/auth/mfa/reset` with their password and a
current TOTP or unused recovery code. Enrollment, successful and failed challenges,
and resets are recorded in the audit log.
