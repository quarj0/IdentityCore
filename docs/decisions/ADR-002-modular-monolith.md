# ADR-002: Modular Monolith Architecture

**Status:** Accepted

**Date:** 2026-07-04

---

# Context

IdentityCore is expected to evolve into a large identity verification platform supporting:

- Multi-tenancy
- AI-powered verification
- Identity document processing
- Biometric verification
- Consent management
- Audit logging
- Webhooks
- Multiple frontend applications
- External provider integrations
- Future government and enterprise deployments

One of the earliest architectural decisions is whether to build the backend as:

- A monolith
- A modular monolith
- Microservices

Choosing too much complexity too early can significantly slow development, while choosing an architecture that is too simple may make future scaling difficult.

---

# Decision

IdentityCore will adopt a **Modular Monolith** architecture for Version 1.0.

The backend will be implemented as a single Django application composed of multiple independent domain modules.

Each module owns its business logic, models, services, permissions, API endpoints, and tests.

Modules communicate through well-defined service interfaces rather than direct coupling wherever practical.

---

# Architecture

Example structure:

```id="yzewtn"
backend/

apps/

accounts/
organizations/
tenants/
verification_subjects/
verifications/
documents/
biometrics/
consent/
policies/
audit/
providers/
webhooks/
notifications/
```

Each module is responsible for its own domain.

Example:

```id="2cq1jp"
verifications/

models.py
services.py
selectors.py
serializers.py
permissions.py
tasks.py
views.py
urls.py
tests/
```

Business logic should remain inside the owning module.

---

# Rationale

A modular monolith provides the advantages of both traditional monoliths and microservices while avoiding much of their complexity.

Benefits include:

- Faster development.
- Easier debugging.
- Simpler deployments.
- Single database transactions.
- Lower operational cost.
- Easier local development.
- Clear domain ownership.
- Ability to extract services later if required.

For an early-stage platform, these advantages outweigh the operational flexibility of a microservices architecture.

---

# Module Communication

Modules should communicate through:

- Service layer methods
- Domain events (where appropriate)
- Shared interfaces

Avoid direct coupling to another module's internal implementation.

Example:

Preferred:

```python id="pgsh39"
verification_service.create_verification(...)
```

Avoid:

```python id="0g8qeu"
Verification.objects.create(...)
```

from unrelated modules.

---

# Database Strategy

The modular monolith uses:

- One PostgreSQL database.
- Shared schema.
- Separate logical domains.

Database ownership follows domain boundaries rather than physical database separation.

---

# Why Not Microservices?

Microservices were rejected for Version 1.0 because they introduce significant operational complexity, including:

- Distributed transactions.
- Service discovery.
- Network latency.
- Inter-service authentication.
- Independent deployments.
- More complex debugging.
- Increased infrastructure costs.
- Distributed tracing requirements.

These challenges provide little value during the MVP stage.

---

# Service Extraction Strategy

The architecture should allow selected modules to be extracted into independent services when justified.

Potential future candidates include:

- AI Service (already separate)
- Notifications
- Reporting
- Search
- Analytics
- Fraud Detection

Extraction should occur only when driven by measurable operational or scalability requirements.

---

# Domain Ownership

Every domain module owns:

- Models
- Business logic
- Validation
- Permissions
- Background tasks
- API contracts
- Tests

Other modules should interact through public service interfaces rather than internal implementation details.

---

# Consequences

## Positive

- Faster feature development.
- Lower infrastructure complexity.
- Easier onboarding for new developers.
- Simpler testing.
- Strong transactional consistency.
- Easier debugging.
- Lower hosting costs.
- Clear domain separation.

## Negative

- Larger deployment unit.
- Shared database requires discipline.
- Poor module boundaries can create tight coupling.
- Independent scaling of individual modules is limited.

These trade-offs are acceptable for Version 1.0.

---

# Alternatives Considered

## Traditional Monolith

Rejected because business logic tends to become tightly coupled over time.

A modular monolith provides stronger separation between domains.

---

## Full Microservices

Rejected due to unnecessary operational complexity during early development.

Microservices may become appropriate for selected domains in the future.

---

## Serverless Architecture

Rejected because long-running AI tasks, background processing, and complex verification workflows are not an ideal fit for a fully serverless architecture.

Serverless may still be appropriate for selected supporting functions in the future.

---

# Migration Strategy

IdentityCore should remain deployable as a single application until clear evidence supports extracting a module.

Examples of such evidence include:

- Independent scaling requirements.
- Different release cycles.
- Team ownership boundaries.
- Performance bottlenecks.
- Infrastructure isolation requirements.

Extraction should preserve existing API contracts wherever possible.

---

# Implementation Notes

- Every domain should be implemented as a Django app.
- Business logic belongs in the service layer.
- Tenant isolation must be enforced across all modules.
- Modules should avoid circular dependencies.
- Shared utilities belong in common libraries, not domain modules.

---

# References

- Architecture
- Database Design
- Coding Standards
- Deployment
- Testing Strategy
