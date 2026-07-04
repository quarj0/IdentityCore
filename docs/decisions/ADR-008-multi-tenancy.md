# ADR-008: Shared Database Multi-Tenancy Strategy

**Status:** Accepted

**Date:** 2026-07-04

---

# Context

IdentityCore is designed as a Software-as-a-Service (SaaS) platform where multiple independent organizations use the same application.

Examples of organizations include:

- Banks
- Universities
- Employers
- Healthcare providers
- Government agencies
- Security companies

Each organization must operate independently and must never be able to access another organization's data.

The platform requires a multi-tenancy strategy that provides strong logical isolation while remaining operationally efficient.

---

# Decision

IdentityCore will implement a **shared database, shared schema** multi-tenancy architecture.

All organizations will use the same PostgreSQL database and schema.

Data isolation will be enforced at the application layer through strict tenant-aware access controls.

Every tenant-owned resource must belong to exactly one tenant.

---

# Tenant Ownership

Every tenant-owned model must reference its owning tenant.

Examples:

```id="a3n9pf"
Organization
        ↓
Tenant
        ↓
Verification Subject
        ↓
Verification
        ↓
Identity Document
        ↓
Audit Event
```

Tenant ownership must be explicit rather than inferred.

---

# Data Isolation

Every request accessing tenant-owned resources must validate:

- Authenticated identity
- Tenant context
- Resource ownership
- Role permissions

Tenant filtering is mandatory for every tenant-owned query.

No exceptions are permitted.

---

# Request Flow

```id="epr42n"
Client Request
        ↓
Authentication
        ↓
Resolve Tenant
        ↓
Authorization
        ↓
Tenant Filtering
        ↓
Business Logic
        ↓
Database Query
```

Tenant resolution occurs before business logic execution.

---

# Public APIs

Every public API request must operate only within the authenticated tenant.

Examples:

```id="6nsvu6"
GET /api/v1/verifications/ver_01...

↓

Authenticated Tenant

↓

Verification belongs to tenant?

↓

Yes → Continue

No → Return 404
```

Returning `404 Not Found` for inaccessible tenant resources reduces information disclosure.

---

# Background Tasks

Tenant context must be preserved in asynchronous processing.

Celery tasks should receive:

- Tenant Public ID
- Resource Public ID

Tasks must never assume tenant ownership based solely on resource identifiers.

---

# Internal Services

Internal services such as the FastAPI AI service do not determine tenant ownership.

The Django backend remains responsible for:

- Tenant validation
- Authorization
- Access control

The AI service processes only media explicitly provided by the backend.

---

# Database Queries

Tenant filtering should be explicit.

Preferred:

```python id="ngv2qk"
Verification.objects.get(
    tenant=tenant,
    public_id=verification_public_id
)
```

Avoid:

```python id="axnbyo"
Verification.objects.get(
    public_id=verification_public_id
)
```

Every tenant-owned query must include tenant context.

---

# Audit Events

Audit Events must include:

- Tenant
- Actor
- Resource
- Timestamp
- Action

This enables tenant-specific auditing while maintaining platform-wide observability.

---

# Caching

Cached data must be tenant-aware.

Cache keys should include tenant identifiers.

Example:

```id="8t6dgb"
tenant:ten_01J...:verification:ver_01J...
```

Tenant context must never be omitted from cache keys.

---

# Search

Search functionality must operate only within the requesting tenant.

Search indexes should preserve tenant isolation.

Cross-tenant searching is prohibited unless explicitly performed by authorized platform administrators.

---

# Monitoring

Monitoring systems should detect:

- Cross-tenant access attempts
- Tenant filtering failures
- Unauthorized resource access
- Permission violations

Security alerts should be generated for repeated isolation failures.

---

# Security

Tenant isolation is considered a primary security boundary.

All components must preserve tenant isolation, including:

- REST APIs
- GraphQL
- Celery workers
- AI processing
- Webhooks
- Object storage access
- Audit queries
- Dashboard interfaces

---

# Enterprise Deployments

Future enterprise customers may require stronger isolation.

Potential deployment options include:

- Dedicated database
- Dedicated infrastructure
- Dedicated object storage
- Dedicated Kubernetes namespace
- Private cloud deployment

The shared-schema architecture should not prevent these future deployment models.

---

# Government Deployments

Government customers may require:

- Dedicated infrastructure
- Data residency
- Air-gapped environments
- Separate operational boundaries

These deployments may use one tenant per deployment rather than a shared SaaS model.

The application architecture should support both approaches.

---

# Consequences

## Positive

- Simple operational model.
- Lower infrastructure cost.
- Easier maintenance.
- Easier upgrades.
- Single deployment pipeline.
- Efficient resource utilization.
- Faster onboarding of new organizations.

## Negative

- Strong application discipline is required.
- Tenant filtering mistakes can be severe.
- Additional testing requirements.
- Large enterprise customers may eventually require dedicated deployments.

These trade-offs are acceptable for Version 1.0.

---

# Alternatives Considered

## Database Per Tenant

Rejected because:

- Operational complexity increases significantly.
- Backups become more difficult to manage.
- Schema migrations become harder.
- Infrastructure costs increase.

This approach may be appropriate for specific enterprise deployments in the future.

---

## Schema Per Tenant

Rejected because:

- Migration complexity grows rapidly.
- Large tenant counts become difficult to manage.
- Tooling becomes more complicated.

Shared schema provides a better balance for Version 1.0.

---

## No Multi-Tenancy

Rejected because IdentityCore is designed as a multi-organization platform from its inception.

Supporting only single-organization deployments would significantly reduce the platform's flexibility.

---

# Future Considerations

Future enhancements may include:

- PostgreSQL Row-Level Security (RLS)
- Dedicated tenant databases
- Dedicated storage
- Tenant-specific encryption keys
- Tenant-specific infrastructure
- Regional tenant deployments

These enhancements should preserve existing business logic wherever possible.

---

# Implementation Notes

- Every tenant-owned model includes a tenant reference.
- Every tenant-owned query filters by tenant.
- Every cache key includes tenant context.
- Every asynchronous task carries tenant context.
- Every audit event records tenant ownership.
- Tenant isolation tests are mandatory for every new tenant-owned feature.

---

# References

- Architecture
- Database Design
- Security
- Threat Model
- Coding Standards
- Testing Strategy
- ADR-002: Modular Monolith Architecture
- ADR-005: PostgreSQL as the Primary Database
