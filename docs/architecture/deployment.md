# Deployment

## IdentityCore

**Version:** 1.0

---

## Purpose

This document defines the deployment strategy for IdentityCore Version 1.0.

IdentityCore must be deployable locally for development, in cloud environments for MVP production, and eventually in private cloud or government-controlled infrastructure.

The deployment design must support security, reliability, observability, backups, rollback, and future scaling.

---

## Deployment Principle

IdentityCore should be easy to run locally, safe to deploy, and flexible enough to move between cloud providers.

The platform should avoid unnecessary infrastructure complexity during the MVP while keeping a clear path toward enterprise and government-grade deployments.

---

## Deployment Environments

IdentityCore will support the following environments:

```text
local
development
staging
production
enterprise
government_on_premise
```

---

## Local Environment

Used by developers.

Purpose:

* Build features
* Run tests
* Debug services
* Develop APIs
* Work without cloud dependency

Local deployment uses Docker Compose.

Services:

```text
django-backend
fastapi-ai
postgres
redis
celery-worker
celery-beat
frontend-dashboard
verification-portal
developer-portal
object-storage-local
```

Example command:

```bash
docker compose up --build
```

Local service access:

```text
Django   -> http://localhost:8000
AI       -> http://localhost:8001
Postgres -> localhost:5433 (container port 5432)
Redis    -> localhost:6379
```

---

## Development Environment

Used for shared engineering testing.

Purpose:

* Test integrated features
* Validate API behavior
* Test frontend/backend integration
* Run early QA

Characteristics:

* Uses test data only
* May reset frequently
* Not used for real Verification Subjects
* Lower infrastructure cost

---

## Staging Environment

Used as production rehearsal.

Purpose:

* Test releases before production
* Run migrations safely
* Validate deployment process
* Test webhooks
* Test monitoring
* Test rollback

Staging should mirror production as closely as possible.

---

## Production Environment

Used for real customers and real verification workflows.

Requirements:

* HTTPS
* Managed database
* Managed Redis or reliable Redis deployment
* Private object storage
* Centralized logging
* Monitoring
* Backups
* Alerts
* Secure secrets management
* Strict access control

---

## Government On-Premise Environment

Future deployment option.

Used when a government or large enterprise requires the platform to run in their own infrastructure.

May require:

* Private network
* Dedicated database
* Dedicated object storage
* No public internet exposure
* SIEM integration
* HSM integration
* Local identity provider
* Strict data residency
* Offline or limited-connectivity support

Government on-premise deployment is outside Version 1.0 but should be considered in architectural decisions.

---

## High-Level Deployment Architecture

```text
Internet
   |
   v
DNS / CDN / DDoS Protection
   |
   v
Reverse Proxy / Load Balancer
   |
   +----------------------+
   |                      |
   v                      v
Django Backend        Frontend Apps
   |
   +----------------------+
   |                      |
   v                      v
PostgreSQL             Redis
   |
   v
Celery Workers
   |
   v
FastAPI AI Service
   |
   v
Object Storage
```

---

## Services

## Django Backend

Responsibilities:

* REST API
* GraphQL API
* Authentication
* Tenant isolation
* Verification workflow
* Audit logging
* Webhooks
* Admin and organization dashboard API

Deployment:

* Containerized
* Stateless
* Horizontally scalable
* Behind reverse proxy

---

## FastAPI AI Service

Responsibilities:

* Face detection
* Face matching
* Liveness checks
* Document OCR
* Document quality checks

Deployment:

* Internal-only service
* Not exposed publicly
* May require CPU optimization
* GPU optional in future

---

## Celery Worker

Responsibilities:

* AI job orchestration
* OCR processing tasks
* Webhook delivery
* Email notifications
* Retention cleanup
* Verification expiry jobs

Deployment:

* Separate container
* Horizontally scalable
* Queue-based processing

---

## Celery Beat

Responsibilities:

* Scheduled tasks
* Verification expiry checks
* Retention cleanup
* Periodic reporting jobs

Deployment:

* Single active instance
* Must avoid duplicate schedulers

---

## PostgreSQL

Responsibilities:

* Core platform data
* Verification metadata
* Audit events
* Policies
* Users
* Tenants
* Decisions

Deployment:

* Managed PostgreSQL preferred for MVP
* Encrypted storage
* Automated backups
* Point-in-time recovery where possible

---

## Redis

Responsibilities:

* Celery broker
* Cache
* Rate limiting
* Short-lived tokens
* Temporary state

Deployment:

* Managed Redis preferred for production
* Persistence depends on usage
* Should be protected from public access

---

## Object Storage

Responsibilities:

* Document captures
* Selfie captures
* Liveness media
* Temporary uploads

Options:

```text
S3
Cloudflare R2
MinIO
Government private object storage
```

Requirements:

* Private buckets
* Encryption
* Signed upload URLs
* Signed download URLs
* Retention cleanup

---

## Frontend Deployment

IdentityCore includes multiple frontend applications:

```text
admin-dashboard
organization-dashboard
verification-portal
developer-portal
```

Recommended deployment:

* Next.js applications
* Deployed separately from backend
* HTTPS enforced
* Environment-specific API base URLs

Possible platforms:

* Vercel for MVP
* Cloudflare Pages
* Self-hosted Node server
* Static export where applicable

---

## Network Security

Production services should follow these rules:

* Only reverse proxy/load balancer exposed publicly.
* PostgreSQL must not be publicly accessible.
* Redis must not be publicly accessible.
* FastAPI AI service must not be publicly accessible.
* Internal services should communicate over private network where possible.
* Admin interfaces should support IP/network restrictions where practical.

---

## Environment Variables

Sensitive configuration should be provided through environment variables or a secrets manager.

Examples:

```text
DATABASE_URL
REDIS_URL
SECRET_KEY
JWT_SIGNING_KEY
ENCRYPTION_KEY
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
EMAIL_PROVIDER_API_KEY
WEBHOOK_SIGNING_SECRET
AI_SERVICE_URL
```

Rules:

* Never commit secrets to Git.
* Use separate secrets per environment.
* Rotate secrets periodically.
* Restrict access to production secrets.

---

## CI/CD Pipeline

Recommended flow:

```text
Developer pushes code
        |
        v
GitHub Actions
        |
        v
Lint
        |
        v
Run tests
        |
        v
Build Docker images
        |
        v
Run security scans
        |
        v
Push images to registry
        |
        v
Deploy to staging
        |
        v
Run smoke tests
        |
        v
Manual approval
        |
        v
Deploy to production
```

---

## Deployment Steps

A production deployment should perform:

1. Pull latest container image.
2. Apply environment configuration.
3. Run database migrations.
4. Start application containers.
5. Run health checks.
6. Run smoke tests.
7. Monitor logs and metrics.
8. Roll back if health checks fail.

---

## Database Migrations

Migration rules:

* Migrations must be reviewed.
* Migrations must be tested in staging.
* Destructive migrations require special approval.
* Large migrations should be backward compatible.
* Production migrations should be auditable.

Recommended approach:

```text
expand
deploy
migrate data
contract
```

This avoids downtime during schema changes.

---

## Health Checks

Every service should expose health checks.

Django backend:

```text
GET /api/v1/health
```

FastAPI AI service:

```text
GET /v1/health
```

Health checks should verify:

* Service is running
* Database connection
* Redis connection
* Object storage connectivity
* AI model availability where applicable

---

## Logging

Production logging must be centralized.

Logs should include:

* Request ID
* Tenant ID
* Actor type
* Service name
* Endpoint
* Status code
* Duration
* Error code

Logs must not include:

* API secrets
* Passwords
* Session tokens
* Raw biometric data
* Full document numbers

---

## Monitoring

Minimum monitoring:

* API uptime
* Error rate
* Response time
* Database CPU/memory/storage
* Redis health
* Celery queue depth
* Worker failures
* Webhook failures
* AI processing latency
* Storage usage
* Failed login attempts

---

## Alerting

Alerts should be configured for:

* API downtime
* High error rate
* Database unavailable
* Redis unavailable
* High queue backlog
* Webhook delivery failures
* Storage failures
* Abnormal login failures
* Cross-tenant access attempts
* Failed backups

---

## Backups

Backup requirements:

* Automated database backups
* Encrypted backups
* Regular backup verification
* Point-in-time recovery where possible
* Backup access restrictions

Object storage backups should follow retention and compliance requirements.

---

## Disaster Recovery

Disaster recovery planning should define:

* Recovery Time Objective
* Recovery Point Objective
* Backup restoration process
* Incident communication process
* Service restoration order

Suggested MVP targets:

```text
RTO: 4 hours
RPO: 24 hours
```

These targets may become stricter for enterprise customers.

---

## Rollback Strategy

Every deployment should support rollback.

Rollback may include:

* Reverting container image
* Reverting environment configuration
* Disabling feature flags
* Pausing background workers
* Rolling forward with a fix

Database rollbacks are risky and should be avoided where possible.

Backward-compatible migrations are preferred.

---

## Scaling Strategy

Version 1.0 scaling approach:

```text
Scale Django horizontally
Scale Celery workers horizontally
Scale FastAPI AI workers separately
Use managed PostgreSQL
Use managed Redis
Use object storage for media
```

AI workloads may require separate scaling from ordinary API workloads.

---

## Resource Isolation

AI workloads can be CPU- or memory-heavy.

Therefore:

* AI service should run separately from Django.
* Celery workers for AI jobs may be separated from webhook/email workers.
* Future GPU workers should be isolated.

Example queues:

```text
default
ai_processing
webhooks
notifications
retention
```

Implementation note:

* The current Docker Compose stack runs a dedicated `celery-worker-ai` service for the `ai_processing` queue.

* The current Django/Celery setup routes webhook processing tasks to the `webhooks` queue and email notification tasks to the `notifications` queue.
* Verification expiry, expired-session cleanup, and retention cleanup tasks run on the `retention` queue.
* Celery beat schedules periodic processing for pending webhook and notification deliveries, verification expiry, expired session cleanup, and retention cleanup.
* The local Docker Compose stack runs separate workers for `default`, `ai_processing`, `webhooks`, `notifications`, and `retention` so lightweight delivery jobs are isolated from general background work.
* The compose stack also defines health checks for each worker role and queue-specific log entry points so worker failures are easier to spot during local operations.

---

## Feature Flags

Feature flags should be used for:

* New AI models
* New verification flows
* New providers
* New document types
* New dashboard features

Feature flags allow gradual rollout and safe rollback.

---

## Secrets Rotation

Production deployment must support rotating:

* API signing keys
* JWT signing keys
* Object storage keys
* Provider credentials
* Database credentials
* Webhook secrets

Rotation should not require full system downtime.

---

## Release Strategy

Recommended release types:

```text
patch
minor
major
hotfix
```

Semantic versioning should be used.

Example:

```text
1.0.0
1.0.1
1.1.0
2.0.0
```

---

## Production Readiness Checklist

Before production launch:

* HTTPS enabled
* Database backups configured
* Redis secured
* Object storage private
* Environment secrets configured
* Admin MFA enabled
* API rate limiting enabled
* Audit logging enabled
* Error tracking enabled
* Monitoring enabled
* Health checks enabled
* Smoke tests passing
* Retention cleanup configured
* Webhook signing enabled
* Security headers configured

---

## MVP Hosting Recommendation

For early MVP:

```text
Frontend:
Vercel or Cloudflare Pages

Backend:
VPS or container platform

Database:
Managed PostgreSQL

Redis:
Managed Redis

Object Storage:
S3-compatible storage

Monitoring:
Sentry + uptime monitoring + basic metrics
```

This keeps the MVP simple while avoiding unnecessary Kubernetes complexity.

---

## Future Infrastructure

Future versions may support:

* Kubernetes
* Helm charts
* Terraform
* Multi-region deployment
* Private cloud deployment
* Government data center deployment
* HSM integration
* SIEM integration
* GPU inference nodes
* Dedicated tenant infrastructure

---

## Version 1.0 Deployment Scope

Version 1.0 includes:

* Docker Compose local development
* Containerized Django backend
* Containerized FastAPI AI service
* PostgreSQL
* Redis
* Celery workers
* Celery beat
* Object storage
* Frontend deployment
* Health checks
* Logging
* Backups
* Monitoring
* Rollback plan

Version 1.0 excludes:

* Kubernetes requirement
* Multi-region production
* GPU cluster requirement
* Government on-premise deployment
* Automated Terraform production infrastructure
* Zero-downtime guarantee
* Dedicated tenant infrastructure

---

## Final Deployment Principle

IdentityCore deployment must balance simplicity and seriousness.

The MVP should be simple enough to operate with a small team, but disciplined enough to protect sensitive identity data, support reliable verification workflows, and evolve into enterprise or government-grade infrastructure without a full rewrite.
