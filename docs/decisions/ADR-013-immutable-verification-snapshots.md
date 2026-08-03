# ADR-013: Freeze policy and workflow configuration at verification creation

## Status

Accepted

## Decision

When a verification is created from an active policy, IdentityCore copies both
the policy definition and its published workflow version into encrypted,
verification-owned snapshots. Evidence and verification responses use these
stored snapshots rather than reading current tenant configuration.

## Consequences

Editing or republishing a policy or workflow cannot change an in-flight
verification or alter the configuration used to interpret its evidence. New
verifications receive the newest selected version. Verifications created
without a policy retain empty snapshots and continue to use their existing
compatibility behavior.
