# System Architecture

> This document describes the current implementation architecture.
> For the canonical platform architecture and long-term architectural model, see `/ARCHITECTURE.md`.

## Status

This document describes the current repository implementation. It is not the full canonical architecture, which is documented in `/ARCHITECTURE.md`.

IdentityCore is implemented as a modular vendor-neutral identity infrastructure platform. Identity verification is the first workload built on the platform. Applications, SDKs, CLI tooling, hosted journeys, and operator consoles integrate with IdentityCore rather than directly with OCR, liveness, face matching, registry, storage, or other provider services.

The current repository contains:

- a Django modular monolith for core control and execution domains;
- a FastAPI service for IdentityCore Managed Providers;
- Celery workers for asynchronous tasks;
- Redis for queues, caching, and coordination;
- PostgreSQL for tenant, workflow, provider, evidence, decision, audit, and subject data;
- S3-compatible object storage for media, raw evidence artifacts, and provider assets;
- frontend applications for hosted journeys, developer docs, organization dashboards, and platform administration;
- Python, JavaScript/TypeScript, Java, and .NET SDKs plus a Python CLI;
- public REST APIs and internal GraphQL boundaries.

## Purpose

This document explains the current implementation architecture and how the repository realizes IdentityCore as a platform infrastructure implementation.

The emphasis is on the existing code structure, provider runtime behavior, provider execution path, and current workload composition. It does not redefine the canonical platform model in `/ARCHITECTURE.md`.

## Implementation structure

IdentityCore is implemented in this repository as:

- a modular Django monolith for control-plane and execution-plane domains;
- a separate FastAPI Managed Provider host for selected internal capability implementations;
- Celery workers for background processing and retries;
- Redis for Celery broker, cache, and runtime coordination;
- PostgreSQL for transactional state, evidence meta, audit, policies, providers, and configuration;
- S3-compatible object storage for submitted media, evidence artifacts, and transient provider payloads;
- frontend apps for verification journeys, developer portal, platform administration, and operator consoles;
- SDKs and CLI tooling for application integration and operational automation.

## Platform architecture

```text
Applications and Portals
        |
        v
IdentityCore APIs
        |
        +--> Control-plane domains
        |
        +--> Execution-plane domains
                  |
                  v
           Provider Runtime
                  |
                  v
               Providers
```

### Control Plane

The Control Plane manages configuration and governance. It includes:

- tenants, organizations, projects, environments;
- users, roles, API clients, scopes, and authorization;
- versioned workflows, templates, and policies;
- provider records, capability declarations, assignments, and health metadata;
- privacy, retention, legal-hold, and export settings;
- audit policy, webhook configuration, and platform administration.

The current repository includes substantial foundations for tenant and environment isolation, workflows, policies, provider records, API clients, audit, privacy operations, dashboards, and admin tooling.

### Execution Plane

The Execution Plane processes workload operations. It includes:

- workflow engine and workflow snapshots;
- policy engine and policy snapshots;
- provider runtime invocation;
- evidence normalization and lineage;
- decision engine and decision input snapshots;
- Manual Review and maker-checker controls;
- audit events, notifications, and webhooks.

A current execution path typically:

1. resolves tenant, project, environment, and subject context;
2. loads immutable workflow and policy snapshots;
3. determines required capabilities and evidence;
4. resolves a provider assignment for each capability;
5. grants only the evidence access needed for the invocation;
6. invokes the provider through the Provider Runtime;
7. validates, normalizes, versions, and persists the result as evidence;
8. evaluates policy and decision rules;
9. routes to retry, fallback, more evidence, or Manual Review;
10. records decision inputs and outcomes;
11. emits audit events, notifications, and signed webhooks;
12. applies retention, export, and deletion controls.

## Provider Runtime

The Provider Runtime is the current execution boundary between IdentityCore and capability providers. It is central to the implementation and is used for IdentityCore Managed Providers as well as external providers.

It is responsible for:

- resolving the selected provider and provider adapter;
- validating capability contracts and compatibility;
- building minimal provider requests;
- applying authentication, signing, timestamps, nonces, and idempotency;
- enforcing endpoint allowlisting, timeout, response-size, and egress controls;
- recording each provider check and attempt;
- normalizing vendor-specific output into versioned IdentityCore evidence;
- redacting sensitive telemetry;
- returning deterministic success or failure semantics;
- supporting retry, fallback, and Manual Review paths.

The repository currently includes adapter-backed managed provider execution, centralized provider invocation, secure HTTP provider calls, message signing, timestamp and nonce validation, replay protection, normalized results, redacted telemetry, duration tracking, and versioned provider outcomes. More advanced conditional provider routes, ordered fallback chains, provider marketplace discovery, and full conformance tooling remain areas of ongoing development.

See [Provider Runtime](provider-runtime.md).

## FastAPI Managed Provider host

The separate `backend/ai-service/` FastAPI service hosts selected IdentityCore Managed Providers such as document quality, document classification, OCR, face comparison, liveness, and presentation-attack detection.

This service is the default host for managed provider implementations. It is not a privileged platform subsystem; it is one provider implementation behind the same runtime boundary used by commercial, government, or customer-hosted providers.

Managed Providers must conform to the same capability, evidence, failure, versioning, and audit expectations as other providers.

## Capability contracts and provider ecosystem

A capability is a stable operation IdentityCore requests from a provider, such as `document.ocr`, `document.quality`, `biometric.face-match`, or `biometric.liveness`.

Capabilities are implemented through versioned contracts. A provider may support one or more capability versions.

The current implementation supports:

- provider adapter registry and provider records;
- capability contract versioning;
- provider checks with capability, contract, provider, and adapter metadata;
- secure HTTP provider integration;
- signed provider requests;
- timestamp and nonce validation;
- replay protection;
- normalized provider results;
- redacted request/response metadata;
- provider assignment foundations.

Provider categories in the current repository include:

- IdentityCore Managed Providers;
- commercial verification and specialist capability providers;
- government and authoritative registries;
- customer-hosted provider services;
- storage providers;
- KMS/HSM and key management providers;
- messaging and notification providers.

Current runtime limitations include richer conditional provider routes, ordered fallback chains, provider health-based selection, and full provider manifest discovery.

## Identity Verification Workload Flow

> Identity Verification Workload Flow

This flow describes the current verification workload as one implementation of the platform. It does not define the entire IdentityCore architecture.

```text
Verification request
        |
        v
workflow and policy snapshot
        |
        v
capability selection and provider assignment
        |
        v
provider runtime invocation
        |
        v
normalized evidence
        |
        v
policy evaluation and decision input
        |
        v
automatic decision or Manual Review
        |
        v
audit, webhook, retention, and export
```

## REST and GraphQL boundaries

The public integration surface is the REST API. Internal dashboards and developer/admin surfaces use GraphQL where appropriate.

The current implementation treats REST as the stable external contract and GraphQL as an internal application boundary.

## Modular monolith and service extraction

The Django backend is organized as a modular monolith to minimize early service complexity while preserving clear domain boundaries.

The current repository supports service extraction through well-defined Django apps, provider adapters, and a separate managed provider host. It is designed to allow future decomposition without changing core workflow, policy, evidence, or provider-runtime semantics.

## Background jobs and observability

Celery workers process asynchronous and long-running tasks such as webhook delivery, retention cleanup, evidence processing, and review notifications. Identity document and biometric work uses database-backed jobs with leases, heartbeats, bounded attempts, and terminal Manual Review routing; the operational procedure is documented in [Processing job recovery](../operations/processing-job-recovery.md).

The current implementation includes observability foundations for provider invocation counts, latency, normalized status, route decisions, evidence creation, decision outcomes, webhook delivery, and deletion jobs. Logs and telemetry are redacted to avoid raw identity data, document images, biometric templates, provider secrets, or unrestricted provider payloads.

## Storage and multi-tenancy

Submitted media and raw evidence artifacts are stored in S3-compatible object storage. The implementation also uses PostgreSQL for metadata and Redis for runtime coordination.

Tenant, organization, project, and environment isolation are implemented across API requests, workflow execution, provider configuration, evidence, decisions, Manual Review, and audit.

Sandbox and production environments are separated to prevent sandbox credentials from accessing production providers or data.

## Security and provider trust

The implementation includes secure provider invocation controls, provider credential encryption, endpoint validation, timestamp and nonce checks, replay protection, signed messages, response validation, timeout enforcement, and schema validation.

Provider trust boundaries are explicitly modeled, with managed-provider isolation and customer-hosted provider risk framed as part of the same runtime boundary.

## Implementation maturity

The current repository presents a working implementation foundation for vendor-neutral identity infrastructure. It includes:

- tenant, project, and environment isolation;
- provider runtime and managed provider host;
- workflow and policy snapshots;
- normalized evidence and provider checks;
- decision recording and Manual Review;
- audit events, retention, deletion, and export controls;
- REST API, GraphQL surface, SDKs, CLI, and hosted applications.

It does not claim complete production readiness for all provider types, country coverage, or regulatory regimes. Advanced provider routing, provider marketplace functionality, broad conformance tooling, reusable claims lifecycle, tenant-owned storage routing, and complete production assurance remain ongoing work.

- Notification defaults
- Feature flags and operational toggles
- Revision history and reset-to-default behavior

Organization branding, tenant verification defaults, and document-type choices remain in the organization and tenant domains.

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
