# ADR-003: REST for Public APIs and GraphQL for Internal Applications

**Status:** Accepted

**Date:** 2026-07-04

---

## Context

IdentityCore exposes functionality to multiple types of consumers.

These include:

- Third-party applications
- Mobile applications
- Internal dashboards
- Administrative tools
- Organization dashboards
- Future partner integrations

The platform requires an API strategy that provides:

- Stability for external integrations
- Flexibility for internal applications
- Strong security
- Excellent developer experience
- Long-term maintainability

The primary architectural decision is whether to use REST, GraphQL, or both.

---

## Decision

IdentityCore will expose:

- **REST APIs** for all public and external integrations.
- **GraphQL** for internal frontend applications and administrative interfaces.

GraphQL will not be part of the public API in Version 1.0.

---

## REST Responsibilities

REST is the official public integration interface.

REST APIs will be used by:

- Organizations
- Backend integrations
- Mobile applications
- Third-party developers
- Future SDKs

Examples:

```id="ajx7nn"
POST /api/v1/verifications

GET /api/v1/verifications/{public_id}

POST /api/v1/webhooks

GET /api/v1/policies
```

REST APIs must be:

- Versioned
- Stable
- Backward compatible where practical
- Fully documented
- Suitable for SDK generation

---

## GraphQL Responsibilities

GraphQL is intended for internal applications owned by IdentityCore.

Examples:

- Platform Dashboard
- Organization Dashboard
- Manual Review Interface
- Internal Operations Tools

GraphQL allows frontend applications to request exactly the data they require while reducing unnecessary API requests.

---

## Why REST for External APIs?

REST was selected because it provides:

- Wide industry adoption
- Excellent tooling
- Strong SDK support
- Predictable caching
- Easier API versioning
- Familiarity for developers
- Clear security boundaries

Most organizations integrating with IdentityCore will already be familiar with REST APIs.

---

## Why GraphQL for Internal Applications?

Internal dashboards often require data from multiple domains.

Examples:

A verification details page may require:

- Verification
- Verification Subject
- Identity Documents
- Face Match Result
- Liveness Result
- Consent
- Audit Events
- Organization
- Verification Policy

Using REST may require multiple requests.

GraphQL allows these related resources to be retrieved efficiently in a single request while avoiding over-fetching.

---

## Security Considerations

GraphQL introduces additional security considerations.

IdentityCore will enforce:

- Authentication
- Authorization
- Tenant isolation
- Query depth limits
- Query complexity limits
- Field-level permissions
- Request rate limiting

Public GraphQL access is intentionally excluded from Version 1.0.

---

## API Versioning

REST APIs will use URL versioning.

Example:

```id="jzgm4y"
/api/v1/
/api/v2/
```

GraphQL schemas will evolve through field additions and deprecations rather than URL versioning.

Breaking GraphQL changes should be avoided whenever possible.

---

## Public API Stability

REST APIs are considered long-term contracts.

Changes should prioritize:

- Backward compatibility
- Predictable behavior
- Stable resource naming
- Consistent error responses

Breaking changes should be introduced only in a new API version.

---

## Internal Flexibility

GraphQL is considered an implementation detail of IdentityCore.

The schema may evolve more frequently to support frontend development while maintaining compatibility for internal applications.

---

## Consequences

## Positive

- Stable public integration experience.
- Flexible internal frontend development.
- Reduced network requests for dashboards.
- Better developer experience for external customers.
- Clear separation between external and internal APIs.

## Negative

- Two API technologies must be maintained.
- Additional GraphQL expertise is required.
- GraphQL security requires careful configuration.
- Some business logic is exposed through two interfaces.

These trade-offs are acceptable because each technology is used where it provides the greatest benefit.

---

## Alternatives Considered

## REST Only

Rejected because internal dashboards would require numerous API calls and duplicate endpoint development for complex views.

---

## GraphQL Only

Rejected because:

- Many external developers expect REST.
- API versioning is simpler with REST.
- SDK generation is more mature.
- Security and caching are easier to reason about for public APIs.

---

## gRPC

Rejected for Version 1.0 because external customers primarily integrate over HTTP/HTTPS.

gRPC may be considered later for internal service-to-service communication if required.

---

## Implementation Notes

- REST remains the primary public interface.
- GraphQL remains internal.
- Both interfaces use the same service layer.
- Business logic must never be duplicated between REST and GraphQL.
- Authorization and tenant isolation rules must be identical regardless of interface.

---

## Future Considerations

Future versions may consider:

- Public GraphQL APIs.
- GraphQL subscriptions for live dashboards.
- Persisted GraphQL queries.
- API gateway integration.

These features should be evaluated based on customer demand and operational maturity.

---

## References

- API Specification
- Architecture
- Security
- Coding Standards
- Threat Model
