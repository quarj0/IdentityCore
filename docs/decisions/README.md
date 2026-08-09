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

All current ADRs are accepted. Older records use an inline `**Status:**` field and newer
records use a `## Status` section; both forms are valid, but every ADR must state a status.

| ADR                                                      | Decision                                                            | Status   |
| -------------------------------------------------------- | ------------------------------------------------------------------- | -------- |
| [ADR-001](ADR-001-public-id-strategy.md)                 | Public ID Strategy                                                  | Accepted |
| [ADR-002](ADR-002-modular-monolith.md)                   | Modular Monolith Architecture                                       | Accepted |
| [ADR-003](ADR-003-rest-and-graphql.md)                   | REST for Public APIs and GraphQL for Internal Applications          | Accepted |
| [ADR-004](ADR-004-fastapi-ai-service.md)                 | Dedicated FastAPI AI Service                                        | Accepted |
| [ADR-005](ADR-005-postgresql.md)                         | PostgreSQL as the Primary Database                                  | Accepted |
| [ADR-006](ADR-006-celery-background-jobs.md)             | Celery for Background Processing                                    | Accepted |
| [ADR-007](ADR-007-object-storage.md)                     | Object Storage for Binary Media                                     | Accepted |
| [ADR-008](ADR-008-multi-tenancy.md)                      | Shared Database Multi-Tenancy Strategy                              | Accepted |
| [ADR-009](ADR-009-provider-adapter-pattern.md)           | Provider Adapter Pattern                                            | Accepted |
| [ADR-010](ADR-010-ai-evidence-not-decision.md)           | AI as Evidence, Not Decision                                        | Accepted |
| [ADR-011](ADR-011-verification-state-transitions.md)     | Verification state transitions                                      | Accepted |
| [ADR-012](ADR-012-verification-session-token-scoping.md) | Scope verification session tokens                                   | Accepted |
| [ADR-013](ADR-013-immutable-verification-snapshots.md)   | Freeze policy and workflow configuration at verification creation   | Accepted |
| [ADR-014](ADR-014-idempotent-upload-completion.md)       | Make upload completion idempotent                                   | Accepted |
| [ADR-015](ADR-015-upload-quarantine.md)                  | Quarantine untrusted upload content                                 | Accepted |
| [ADR-016](ADR-016-provider-capability-contract.md)       | Version the provider capability contract                            | Accepted |
| [ADR-017](ADR-017-secure-custom-http-provider.md)        | Secure custom HTTP provider adapter                                 | Accepted |
| [ADR-018](ADR-018-versioned-decision-contract.md)        | Version and persist decision inputs                                 | Accepted |
| [ADR-019](ADR-019-reviewer-assignment.md)                | Claim Manual Reviews atomically                                     | Accepted |
| [ADR-020](ADR-020-maker-checker-decisions.md)            | Require independent approval for high-risk decisions                | Accepted |
| [ADR-021](ADR-021-tamper-evident-audit-chain.md)         | Protect the audit trail with a tenant hash chain                    | Accepted |
| [ADR-022](ADR-022-retention-deletion-controls.md)        | Enforce verified retention deletion with legal holds                | Accepted |
| [ADR-023](ADR-023-data-subject-deletion.md)              | Pseudonymize subject deletion while preserving required audit facts | Accepted |
| [ADR-024](ADR-024-data-subject-export.md)                | Authorized, redacted, expiring subject exports                      | Accepted |
| [ADR-025](ADR-025-centralized-object-authorization.md)   | Centralized Object Authorization                                    | Accepted |

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
