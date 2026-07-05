# System Architecture

## IdentityCore

**Version:** 1.0

---

## Purpose

This document defines the technical architecture for IdentityCore Version 1.0.

IdentityCore is designed as a secure, multi-tenant identity verification platform that supports document capture, selfie capture, liveness detection, face matching, verification decisions, audit logging, REST APIs, GraphQL dashboards, webhooks, and future provider integrations.

The architecture must support a focused MVP while remaining flexible enough to evolve into a larger digital identity infrastructure platform.

---

## Architectural Philosophy

IdentityCore will begin as a modular monolith with clearly separated internal domains.

This avoids unnecessary early microservice complexity while keeping the codebase ready for future service extraction.

The platform should be designed so that major modules can later become independent services without rewriting the entire system.

---

## High-Level Architecture

```text
Verification Subject
        |
        v
Verification Web Portal
        |
        v
IdentityCore API Gateway
        |
        v
Core Platform Backend
        |
        +-------------------------------+
        |                               |
        v                               v
Document Intelligence Service     Biometric Intelligence Service
        |                               |
        v                               v
Object Storage                  Face Matching / Liveness
        |
        v
Verification Decision Engine
        |
        v
Audit & Webhook System
        |
        v
Organization System / External Client
```

---

## Main Applications

## Admin Dashboard

Used by platform administrators to manage the IdentityCore platform.

Responsibilities:

- Manage organizations
- View platform-wide audit logs
- Manage provider configurations
- Monitor system activity
- Manage platform users
- Review system health

---

## Organization Dashboard

Used by customer organizations.

Responsibilities:

- Manage organization users
- Create verification requests
- Configure verification policies
- View verification results
- Review manual verification cases
- Manage API clients
- View organization audit logs
- Configure webhooks

---

## Verification Portal

Used by Verification Subjects.

Responsibilities:

- Open verification link
- View verification purpose
- Accept consent
- Upload identity document
- Capture selfie
- Complete liveness check
- View verification progress

---

## Developer Portal

Used by technical customers.

Responsibilities:

- View API documentation
- Generate API keys
- Configure webhooks
- View API logs
- Test verification endpoints

---

## API Strategy

IdentityCore uses both REST and GraphQL.

## REST API

REST will be used for external integrations.

Examples:

```text
POST /api/v1/verifications
GET  /api/v1/verifications/{verification_id}
POST /api/v1/verifications/{verification_id}/cancel
POST /api/v1/webhooks/test
GET  /api/v1/document-types
GET  /api/v1/country-profiles
```

REST is preferred for:

- External developers
- Organization integrations
- API clients
- Webhooks
- File uploads
- Public API documentation

---

## GraphQL API

GraphQL will be used mainly for internal dashboards.

GraphQL is preferred for:

- Admin dashboard
- Organization dashboard
- Reporting views
- Complex filtering
- Flexible dashboard queries

GraphQL should not replace the public REST API in Version 1.0.

---

## Backend Architecture

Version 1.0 will use Django as the main backend.

The backend will be organized by domain modules.

```text
backend/django/
    identitycore/
        apps/
            accounts/
            organizations/
            tenants/
            access_control/
            verifications/
            verification_sessions/
            documents/
            biometrics/
            consent/
            policies/
            decisions/
            risk/
            providers/
            audit/
            webhooks/
            notifications/
            uploads/
            api_clients/
            billing/
            reporting/
```

---

## Core Backend Modules

## Accounts Module

Responsible for Platform Users.

Responsibilities:

- Authentication
- Password reset
- MFA
- Session management
- User profile
- Account security

---

## Organizations Module

Responsible for customer organizations.

Responsibilities:

- Organization registration
- Organization settings
- Branding
- Organization status
- Default jurisdiction
- Default country profile

---

## Tenants Module

Responsible for tenant isolation.

Responsibilities:

- Tenant resolution
- Tenant-aware queries
- Tenant configuration
- Tenant lifecycle

Business rule:

Every request that accesses organization-owned data must resolve tenant context.

---

## Access Control Module

Responsible for roles and permissions.

Responsibilities:

- Role-based access control
- Permission checks
- Tenant-scoped permissions
- Platform-level permissions
- Sensitive action controls

---

## Verifications Module

Responsible for the main Verification lifecycle.

Responsibilities:

- Create verification
- Track verification status
- Expire verification
- Cancel verification
- Coordinate verification steps
- Store final verification result

---

## Verification Sessions Module

Responsible for subject-facing sessions.

Responsibilities:

- Generate verification links
- Validate session tokens
- Track session progress
- Expire sessions
- Protect subject-facing flows

---

## Documents Module

Responsible for Identity Documents and Document Captures.

Responsibilities:

- Document upload
- Document type classification
- OCR result storage
- Document quality checks
- Document capture metadata

---

## Biometrics Module

Responsible for biometric evidence.

Responsibilities:

- Selfie capture records
- Face match results
- Liveness check results
- Biometric template metadata
- Model version tracking

The module should not expose raw biometric templates through public APIs.

---

## Consent Module

Responsible for consent capture and consent records.

Responsibilities:

- Consent versioning
- Consent acceptance
- Consent metadata
- Consent auditability
- Consent withdrawal handling in future versions

---

## Policies Module

Responsible for verification rules.

Responsibilities:

- Required document types
- Liveness requirements
- Face match thresholds
- Manual review thresholds
- Expiry rules
- Retention rules

---

## Decisions Module

Responsible for Verification Decisions.

Responsibilities:

- Automatic decision rules
- Manual review outcome
- Decision reason codes
- Decision evidence summary
- Decision policy version

---

## Risk Module

Responsible for risk signals.

Responsibilities:

- Detect suspicious attempts
- Device and IP risk signals
- Repeated failures
- Duplicate attempts
- Risk scoring

Version 1.0 should keep this simple and rule-based.

---

## Providers Module

Responsible for external and internal provider adapters.

Responsibilities:

- Normalize provider requests
- Normalize provider responses
- Store provider check metadata
- Handle provider failures
- Support mock providers

Version 1.0 providers:

- Mock Document Provider
- Mock Identity Provider
- Internal Face Match Provider
- Internal Liveness Provider

---

## Audit Module

Responsible for immutable audit events.

Responsibilities:

- Log sensitive actions
- Log authentication events
- Log verification events
- Log API activity
- Log administrative changes
- Support forensic traceability

Audit logs must be treated as high-value security records.

---

## Webhooks Module

Responsible for event delivery to organizations.

Responsibilities:

- Register webhook endpoints
- Sign webhook payloads
- Deliver webhook events
- Retry failed webhooks
- Record webhook attempts

---

## Notifications Module

Responsible for user notifications.

Responsibilities:

- Verification link emails
- Verification status emails
- Manual review notifications
- Security alerts

---

## API Clients Module

Responsible for developer integration credentials.

Responsibilities:

- API key generation
- API secret management
- API scopes
- API usage logging
- API rate limiting

---

## Billing Module

Responsible for future monetization.

Responsibilities:

- Usage tracking
- Verification counts
- Plan limits
- Invoice metadata

Payment processing is outside Version 1.0.

---

## Reporting Module

Responsible for aggregated views.

Responsibilities:

- Verification volume
- Success rate
- Rejection rate
- Manual review rate
- API usage
- Tenant activity

---

## AI Service Architecture

AI-related processing should be isolated from the main Django backend.

Version 1.0 will use a separate FastAPI service.

```text
backend/fastapi-ai/
    app/
        face_detection/
        face_matching/
        liveness/
        document_quality/
        ocr/
        model_registry/
```

## AI Service Responsibilities

- Face detection
- Face embedding generation
- Face comparison
- Liveness detection
- Document quality checks
- OCR processing
- Model version reporting

## AI Service API Examples

```text
POST /v1/face/compare
POST /v1/liveness/check
POST /v1/document/quality
POST /v1/document/ocr
GET  /v1/models
```

## AI Service Rules

- The AI service must not make final business decisions.
- The AI service returns scores, confidence values, and technical results.
- The Django backend makes verification decisions using Verification Policies.
- Every AI result must include model version and processing timestamp.

---

## Data Architecture

## Primary Database

PostgreSQL will be used as the main relational database.

Stores:

- Organizations
- Tenants
- Platform Users
- Roles
- Permissions
- Verifications
- Verification Subjects
- Documents
- Consent records
- Decisions
- Provider checks
- Webhook records
- Configuration

---

## Cache and Queue Backend

Redis will be used for:

- Caching
- Rate limiting
- Celery broker
- Temporary session state
- Short-lived verification tokens

---

## Background Jobs

Celery will be used for asynchronous processing.

Background jobs include:

- OCR processing
- Face matching
- Liveness processing
- Verification expiry
- Webhook delivery
- Email notifications
- Retention cleanup
- Audit processing

---

## Object Storage

Object storage will be used for encrypted media.

Stores:

- Document captures
- Selfie captures
- Liveness media
- Temporary verification uploads

Options:

- S3
- Cloudflare R2
- MinIO
- Government private object storage in future deployments

Raw media must follow retention policies.

---

## Audit Storage

Version 1.0 may store audit events in PostgreSQL.

Future versions may use:

- Append-only log storage
- WORM storage
- Dedicated audit database
- SIEM integration

---

## Verification Flow

```text
1. Organization creates Verification.
2. Platform creates Verification Session.
3. Verification Subject opens secure link.
4. Verification Subject reviews purpose and consent.
5. Verification Subject accepts consent.
6. Verification Subject submits Identity Document.
7. Platform performs document quality and OCR processing.
8. Verification Subject submits Selfie Capture.
9. Platform performs liveness check.
10. Platform performs face match.
11. Risk module evaluates signals.
12. Decision module applies Verification Policy.
13. Verification is marked Verified, Rejected, or Manual Review Required.
14. Audit Events are recorded.
15. Webhook Event is sent to Organization.
```

---

## Multi-Tenancy Architecture

Version 1.0 uses tenant-scoped data isolation.

Every tenant-owned table must include:

```text
tenant_id
```

Tenant context must be applied:

- In API views
- In services
- In database queries
- In audit logs
- In background jobs
- In webhook events

Business rule:

No Platform User or API Client may access data outside their authorized tenant unless explicitly granted platform-level permissions.

---

## Security Architecture

Security is a core architectural requirement.

Minimum controls:

- HTTPS everywhere
- MFA for Platform Users
- Strong password hashing
- JWT or secure session authentication
- API key authentication for external clients
- Scoped API permissions
- Tenant isolation
- Rate limiting
- IP/device logging
- Encryption at rest
- Encryption in transit
- Secure file storage
- Signed webhooks
- Audit logging
- Secrets management
- Admin action logging

---

## Event Architecture

IdentityCore should use domain events internally.

Examples:

```text
verification.created
verification.consent_accepted
document.capture_uploaded
document.ocr_completed
selfie.capture_uploaded
liveness.completed
face_match.completed
verification.manual_review_required
verification.verified
verification.rejected
webhook.delivery_failed
```

Events may trigger:

- Audit logs
- Notifications
- Webhooks
- Background processing
- Reporting updates

Version 1.0 can implement events inside Django using service-layer events and Celery tasks.

Future versions may use Kafka, RabbitMQ, or another event broker.

---

## Provider Adapter Architecture

Provider integrations must use adapter patterns.

```text
Core Platform
    |
    v
Provider Interface
    |
    +--> Mock Identity Provider
    +--> Internal AI Provider
    +--> Third-party KYC Provider
    +--> Government Identity Provider
```

Rules:

- Core business logic must depend on provider interfaces, not provider-specific APIs.
- Provider responses must be normalized.
- Provider failures must not break the entire platform.
- Provider metadata must be auditable.
- Country-specific providers must live outside the core domain logic.

---

## Deployment Architecture

## Local Development

Local development will use Docker Compose.

Services:

- Django backend
- FastAPI AI service
- PostgreSQL
- Redis
- Celery worker
- Celery beat
- Frontend apps
- Object storage emulator or local media storage

---

## MVP Production

Recommended MVP production setup:

- Containerized services
- Managed PostgreSQL
- Managed Redis
- Object storage
- Reverse proxy
- HTTPS
- Centralized logging
- Monitoring
- Automated backups

---

## Future Enterprise Deployment

Future versions should support:

- Kubernetes
- Private cloud
- Government data center deployment
- Dedicated tenant deployments
- SIEM integration
- Hardware security modules
- Private network connectivity
- High availability clusters

---

## Service Extraction Strategy

IdentityCore begins as a modular monolith.

Modules may become services when:

- Scaling needs differ
- Security boundaries require isolation
- Teams need independent deployment
- AI workload becomes heavy
- Provider gateway requires independent uptime
- Audit storage requires separate compliance controls

Likely first services to extract:

```text
1. Biometric Intelligence Service
2. Document Intelligence Service
3. Webhook Delivery Service
4. Audit Service
5. Identity Provider Gateway
```

---

## Recommended Technology Stack

## Backend

- Python
- Django
- Django REST Framework
- Strawberry GraphQL or Graphene
- Celery
- Redis
- PostgreSQL

## AI Service

- Python
- FastAPI
- OpenCV
- InsightFace
- MediaPipe
- ONNX Runtime
- Tesseract or PaddleOCR

## Frontend

- TypeScript
- Next.js
- React
- Tailwind CSS
- shadcn/ui

## Mobile Future

- Flutter
- Dart

## Infrastructure

- Docker
- Docker Compose
- Nginx
- PostgreSQL
- Redis
- S3-compatible object storage
- GitHub Actions

---

## Observability

Version 1.0 should include:

- Structured logs
- Error tracking
- API request logs
- Background job logs
- Verification processing logs
- Webhook delivery logs
- Audit logs
- Basic metrics

Future versions should include:

- Distributed tracing
- SIEM integration
- Prometheus
- Grafana
- OpenTelemetry

---

## Architecture Boundaries

The core platform must not:

- Hardcode Ghana-specific document names.
- Own government identity databases.
- Use face matching as the only decision factor.
- Expose biometric templates through public APIs.
- Store raw media indefinitely.
- Allow tenant data leakage.
- Allow unaudited sensitive actions.

---

## Version 1.0 Architecture Scope

Version 1.0 includes:

- Modular Django backend
- FastAPI AI service
- REST API
- GraphQL dashboard API
- Multi-tenancy
- Authentication
- RBAC
- Verification workflow
- Document capture
- Selfie capture
- Liveness checks
- Face matching
- Consent records
- Verification decisions
- Audit logs
- Webhooks
- Notifications
- Basic reporting
- Provider adapter foundation

Version 1.0 excludes:

- Real government database integrations
- Fingerprint recognition
- Iris recognition
- Criminal records
- Immigration systems
- Digital wallet
- National identity issuance
- Mobile app
- Offline verification
- Kubernetes production requirement

---

## Final Architectural Principle

IdentityCore must be designed as identity infrastructure, not a single-purpose verification application.

The architecture should allow the platform to start small, remain secure, and expand carefully into more complex identity services without compromising privacy, auditability, or tenant isolation.
