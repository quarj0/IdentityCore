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

```id="q5mpml"
ADR-001  Public ID Strategy

ADR-002  Modular Monolith Architecture

ADR-003  REST for Public APIs and GraphQL for Internal Applications

ADR-004  Dedicated FastAPI AI Service

ADR-005  PostgreSQL as the Primary Database

ADR-006  Celery for Background Processing

ADR-007  Object Storage for Binary Media

ADR-008  Shared Database Multi-Tenancy Strategy

ADR-009  Provider Adapter Pattern

ADR-010  AI as Evidence, Not Decision
```

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
