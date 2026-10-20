# Architecture Decision Records (ADRs)

## Purpose

This directory contains the **Architecture Decision Records (ADRs)** for IdentityCore.

An ADR is a permanent record of an important architectural or technical decision made during the development of the platform.

The purpose of an ADR is to answer:

- What decision was made?
- Why was it made?
- What alternatives were considered?
- What are the consequences of the decision?

ADRs preserve the reasoning behind architectural choices so future contributors can understand _why_ the system was designed the way it is.

---

## Why ADRs?

Software architecture evolves over time.

Without documented decisions, future contributors may not understand why certain approaches were chosen and may unintentionally reverse or duplicate previous work.

ADRs help preserve institutional knowledge, improve onboarding, and support long-term maintainability.

---

## When to Create an ADR

Create an ADR when making a significant architectural or engineering decision.

Examples include:

- Choosing a new database technology.
- Introducing a new infrastructure component.
- Changing the authentication strategy.
- Modifying the multi-tenancy approach.
- Introducing a new AI model architecture.
- Changing API design principles.
- Selecting a new messaging system.
- Adopting a new deployment strategy.

Do **not** create ADRs for:

- Minor bug fixes.
- Refactoring without architectural impact.
- Formatting or style changes.
- Small implementation details.
- Temporary experiments.

---

## ADR Lifecycle

Each ADR progresses through one of the following states:

- Proposed
- Accepted
- Superseded
- Deprecated

Most ADRs in IdentityCore will initially move directly from **Proposed** to **Accepted** after review.

If a decision changes in the future, create a new ADR rather than rewriting history.

---

## ADR Format

Every ADR should follow the standard structure:

```id="7w7j2x"
Title

Status

Date

Context

Decision

Rationale

Consequences

Alternatives Considered

Implementation Notes

References
```

Keeping every ADR consistent makes them easier to read and maintain.

---

## Numbering

ADRs use sequential numbering.

Example:

```id="ow4b7d"
ADR-001-public-id-strategy.md

ADR-002-modular-monolith.md

ADR-003-rest-and-graphql.md
```

Numbers are permanent and should never be reused.

If an ADR is removed, its number remains reserved.

---

## Updating Decisions

ADRs should be treated as historical records.

Do **not** rewrite an accepted ADR because the architecture changed.

Instead:

1. Create a new ADR.
2. Reference the previous ADR.
3. Mark the previous ADR as **Superseded** if appropriate.

This preserves the project's architectural history.

---

## Current ADR Index

Read the status in each ADR; acceptance records an architectural decision, not deployment certification.

| ADR | Decision |
| --- | --- |
| [ADR-001](ADR-001-public-id-strategy.md) | ADR-001: Public ID Strategy |
| [ADR-002](ADR-002-modular-monolith.md) | ADR-002: Modular Monolith Architecture |
| [ADR-003](ADR-003-rest-and-graphql.md) | ADR-003: REST for Public APIs and GraphQL for Internal Applications |
| [ADR-004](ADR-004-fastapi-ai-service.md) | ADR-004: Dedicated FastAPI AI Service |
| [ADR-005](ADR-005-postgresql.md) | ADR-005: PostgreSQL as the Primary Database |
| [ADR-006](ADR-006-celery-background-jobs.md) | ADR-006: Celery for Background Processing |
| [ADR-007](ADR-007-object-storage.md) | ADR-007: Object Storage for Binary Media |
| [ADR-008](ADR-008-multi-tenancy.md) | ADR-008: Shared Database Multi-Tenancy Strategy |
| [ADR-009](ADR-009-provider-adapter-pattern.md) | ADR-009: Provider Adapter Pattern |
| [ADR-010](ADR-010-ai-evidence-not-decision.md) | ADR-010: AI as Evidence, Not Decision |
| [ADR-011](ADR-011-verification-state-transitions.md) | ADR-011: Verification state transitions |
| [ADR-012](ADR-012-verification-session-token-scoping.md) | ADR-012: Scope verification session tokens |
| [ADR-013](ADR-013-immutable-verification-snapshots.md) | ADR-013: Freeze policy and workflow configuration at verification creation |
| [ADR-014](ADR-014-idempotent-upload-completion.md) | ADR-014: Make upload completion idempotent |
| [ADR-015](ADR-015-upload-quarantine.md) | ADR-015: Quarantine untrusted upload content |
| [ADR-016](ADR-016-provider-capability-contract.md) | ADR-016: Version the provider capability contract |
| [ADR-017](ADR-017-secure-custom-http-provider.md) | ADR-017: Secure custom HTTP provider adapter |
| [ADR-018](ADR-018-versioned-decision-contract.md) | ADR-018: Version and persist decision inputs |
| [ADR-019](ADR-019-reviewer-assignment.md) | ADR-019: Claim manual reviews atomically |
| [ADR-020](ADR-020-maker-checker-decisions.md) | ADR-020: Require independent approval for high-risk decisions |
| [ADR-021](ADR-021-tamper-evident-audit-chain.md) | ADR-021: Protect the audit trail with a tenant hash chain |
| [ADR-022](ADR-022-retention-deletion-controls.md) | ADR-022: Enforce verified retention deletion with legal holds |
| [ADR-023](ADR-023-data-subject-deletion.md) | ADR-023: Pseudonymize data-subject deletion while preserving required audit facts |
| [ADR-024](ADR-024-data-subject-export.md) | ADR-024: Authorized, redacted, expiring data-subject exports |
| [ADR-025](ADR-025-centralized-object-authorization.md) | ADR-025: Centralized Object Authorization |
| [ADR-026](ADR-026-webhook-delivery-leases.md) | ADR-026: Claim webhook deliveries without locking producers during HTTP |
| [ADR-027](ADR-027-operational-telemetry.md) | ADR-027: Payload-free operational telemetry |
| [ADR-028](ADR-028-encrypted-consistent-backups.md) | ADR-028: Encrypted, quiesced backup sets and isolated restore |
| [ADR-029](ADR-029-concurrent-decisions-and-bearer-proofs.md) | ADR-029: Preserve human decisions and bound bearer authentication cost |
| [ADR-030](ADR-030-provider-manifests-and-promotion.md) | ADR-030: Declare provider coverage and approve environment configuration |
| [ADR-031](ADR-031-external-risk-evidence.md) | ADR-031: External risk providers return evidence only |
| [ADR-032](ADR-032-document-authenticity-and-source-overlays.md) | ADR-032: Versioned authenticity evidence and source-coordinate overlays |
| [ADR-033](ADR-033-atomic-api-usage-quotas.md) | ADR-033: Durable environment API quotas |
| [ADR-034](ADR-034-team-invitation-lifecycle.md) | ADR-034: Tenant invitation lifecycle and encrypted delivery |
| [ADR-035](ADR-035-dashboard-session-revocation.md) | ADR-035: Dashboard session ownership and revocation |
| [ADR-036](ADR-036-icao-mrz-evidence.md) | ADR-036: ICAO MRZ structural evidence |
| [ADR-037](ADR-037-document-consistency-signals.md) | ADR-037: Versioned country-aware document signals |
| [ADR-038](ADR-038-bound-mobile-handoff.md) | ADR-038: One-time mobile handoff capabilities |
| [ADR-039](ADR-039-signed-capture-provenance.md) | ADR-039: Signed capture provenance and replay signals |
| [ADR-040](ADR-040-private-duplicate-and-velocity-signals.md) | ADR-040: Private duplicate and velocity signals |
| [ADR-041](ADR-041-deployment-drain-and-expand-rollouts.md) | ADR 041: Instance drain and expand-only deployment gates |
| [ADR-042](ADR-042-mfa-transaction-and-recovery-bindings.md) | ADR 042: Locked MFA transactions and keyed recovery digests |
| [ADR-043](ADR-043-policy-bound-manual-review-reasons.md) | ADR 043: Policy-bound manual review reasons |
| [ADR-044](ADR-044-explicit-sandbox-simulation.md) | ADR 044: Explicit sandbox outcome simulation |
| [ADR-045](ADR-045-tenant-review-queues.md) | ADR 045: Tenant review queues and fair assignment |
| [ADR-046](ADR-046-independent-review-quality-sampling.md) | ADR 046: Independent review quality sampling |
| [ADR-047](ADR-047-tenant-data-envelopes-and-key-rotation.md) | ADR 047: Tenant data envelopes and resumable key rotation |
| [ADR-048](ADR-048-customer-kms-wrapping.md) | ADR 048: Customer-managed KMS and HSM wrapping |
| [ADR-049](ADR-049-tenant-object-routing.md) | ADR 049: Tenant and environment object storage routing |
| [ADR-050](ADR-050-purpose-bound-consent.md) | ADR 050: Purpose-bound consent and withdrawal |
| [ADR-051](ADR-051-trusted-subject-metadata.md) | ADR 051: Trusted hosted-journey subject metadata |
| [ADR-052](ADR-052-platform-invitation-delivery.md) | ADR 052: Platform administrator invitation delivery |
| [ADR-053](ADR-053-verification-reviewer-permission.md) | ADR 053: Explicit verification reviewer permission |
| [ADR-054](ADR-054-ordered-active-liveness.md) | ADR 054: Ordered and bound active-liveness evidence |
| [ADR-055](ADR-055-scoped-bff-session-credentials.md) | ADR 055: Per-session BFF credentials and retryable exchange |
| [ADR-056](ADR-056-immutable-project-environment.md) | ADR 056: Immutable project environment |
| [ADR-057](ADR-057-upload-transfer-transactions.md) | Short upload transactions and fresh consent at acceptance |

---

## Guiding Principles

Architecture decisions should prioritize:

- Security
- Privacy
- Simplicity
- Maintainability
- Scalability
- Auditability
- Performance
- Developer Experience

Architectural consistency is generally more valuable than adopting new technologies without a clear benefit.

---

## Final Principle

Every significant architectural decision should be documented before or alongside implementation.

A well-maintained ADR history ensures that IdentityCore evolves through deliberate engineering decisions rather than undocumented assumptions.
