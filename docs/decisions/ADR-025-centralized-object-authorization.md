# ADR-025: Centralized Object Authorization

## Status

Accepted

## Date

2026-08-09

## Context

IdentityCore exposes the same tenant-owned resources through REST, GraphQL,
internal services, and Celery tasks. Channel-specific checks had begun to drift:
REST and GraphQL duplicated actor checks, Manual Review separately encoded
ownership, and workers relied on possession of an object identifier.

Authentication proves who or what is calling. It does not decide whether that
actor may perform an action on a specific tenant-owned object.

## Decision

All channels delegate authorization decisions to `common.authorization`.

- User decisions distinguish authenticated, tenant, platform, and Manual Review
  actions and enforce tenant ownership before granting object access.
- API clients require both the declared scopes and a matching tenant.
- Explicit role-permission checks deny when the permission is absent, the role
  is inactive, or the role/assignment is outside the target tenant.
- Service principals contain an allow-list of actions. Per-object work requires
  a tenant-owned resource; cross-tenant batch work must be declared explicitly.
- REST permission classes and GraphQL guards translate the shared decision into
  their protocol-specific response. They do not implement separate policy.

Endpoints that currently authorize any authenticated tenant member may omit a
role permission code. New sensitive operations must declare one. Migrating an
existing operation to role-based authorization requires seeded permissions and
a compatibility plan for existing tenant users.

## Consequences

Authorization behavior is testable without invoking a transport, and the same
decision can be reused by every entry point. Unknown actions, missing roles,
inactive roles, tenant mismatches, missing scopes, and unscoped service calls are
denied by default.

Adding an action now requires defining its actor and tenant semantics once, then
configuring each transport to request that decision. Background jobs must use a
named service principal rather than treating task execution as implicit access.

## Alternatives Considered

- Keep authorization in each view, resolver, and task. This was rejected because
  equivalent resources could acquire inconsistent rules.
- Require role permissions on every existing endpoint immediately. This was
  rejected because existing tenants do not yet have complete role-permission
  seed data; rollout must be incremental and explicit.

## References

- IC-016 / GitHub issue #100
- ADR-008: Shared Database Multi-Tenancy Strategy
