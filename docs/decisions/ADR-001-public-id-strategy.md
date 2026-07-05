# ADR-001: Public ID Strategy

**Status:** Accepted

**Date:** 2026-07-04

---

# Context

IdentityCore exposes resources through public APIs, frontend applications, webhook payloads, and audit records.

Using auto-incrementing database IDs in public interfaces introduces several problems:

- They reveal the approximate number of records.
- They are predictable and easy to enumerate.
- They expose implementation details.
- They create unnecessary security and privacy risks.
- They make future database migrations more difficult.

The platform requires identifiers that are globally unique, difficult to guess, and safe to expose externally.

---

# Decision

IdentityCore will use **prefixed ULIDs** as the public identifier for every externally accessible resource.

Examples:

```text
org_01J...
ten_01J...
usr_01J...
sub_01J...
ver_01J...
ses_01J...
doc_01J...
api_01J...
pol_01J...
aud_01J...
```

Each resource will therefore have:

- An internal database primary key (`id`) used only for database relationships.
- A public identifier (`public_id`) used in APIs, webhooks, URLs, logs, and user interfaces.

Internal database IDs must never be exposed outside trusted internal services.

---

# Rationale

Prefixed ULIDs were selected because they:

- Are globally unique.
- Preserve chronological ordering.
- Are safe to expose publicly.
- Scale well across distributed systems.
- Improve debugging by identifying resource types from their prefixes.
- Avoid exposing database implementation details.

The resource prefix improves readability and reduces ambiguity during development, debugging, and support.

For example:

```text
ver_01J...
```

is immediately recognizable as a Verification identifier, while:

```text
org_01J...
```

clearly identifies an Organization.

---

# Consequences

## Positive

- Public APIs are protected from simple identifier enumeration.
- Resource types are immediately recognizable.
- URLs remain stable even if internal database structures change.
- Future database migrations become easier.
- API responses are more consistent.
- Public identifiers remain immutable.

## Negative

- Additional storage is required for the `public_id` column.
- Database indexes become slightly larger.
- Developers must remember to use `public_id` for external interfaces instead of internal IDs.

These trade-offs are considered acceptable given the security, maintainability, and usability benefits.

---

# Alternatives Considered

## Auto-incrementing Integers

Rejected because they are predictable and expose internal implementation details.

---

## UUID Version 4

Rejected because UUIDv4 values are not naturally sortable, making operational debugging and chronological ordering more difficult.

---

## Slugs

Rejected as primary identifiers because they are mutable, may collide, and often contain business-specific information.

Slugs may be added in the future for human-friendly URLs but will never replace `public_id`.

---

## UUID Version 7

Considered as a future alternative due to its time-ordered characteristics.

At the time of this decision, prefixed ULIDs were chosen because they are mature, well understood, and align with the project's requirements.

---

# Implementation Notes

- Every externally accessible model should include a `public_id`.
- `public_id` values must be generated automatically.
- `public_id` values are immutable after creation.
- APIs, GraphQL, webhooks, and frontend applications must use `public_id`.
- Internal joins and foreign keys continue to use database primary keys.
- The Django implementation now uses strict prefixed ULIDs through a shared helper in `apps.core`.

---

# References

- Database Design
- API Specification
- Coding Standards
- Security
- Threat Model
