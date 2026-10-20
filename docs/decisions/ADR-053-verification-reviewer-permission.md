# ADR 053: Explicit verification reviewer permission

Status: Accepted

Tenant membership alone does not authorize access to verification review queues,
evidence, decisions, checker approval or quality review. Collection and object policy
checks require an active tenant role with `review_verification`, scoped consistently
to the user and case tenant. Inactive/deleted roles or users deny access. Platform
administrators retain platform-owned review access and cannot use that identity to
review tenant-owned cases.

The migration creates the permission and grants it only to existing built-in system
Tenant Administrator, Organization Administrator and Verification Officer roles.
Custom roles require an explicit operator grant. New onboarding administrators and
the local synthetic reviewer fixture receive the permission through their normal role
setup. Do not preserve the old broad membership privilege as a fallback.

Review finalization rechecks current actor authority at the service boundary as well
as request admission. Assignment and maker-checker exclusions remain independent; the
permission never authorizes another tenant, another reviewer assignment, self-review
or an invalid state transition. General verification-case escalation remains separate
future work rather than an implication of this permission.
