# ADR-022: Enforce verified retention deletion with legal holds

## Status

Accepted

## Decision

Retention cleanup is scoped to each verification's policy snapshot and
therefore preserves the configured purpose/environment policy boundary.
Tenant-wide and verification-specific `RetentionLegalHold` records defer
cleanup until released or expired.

Object storage deletion is attempted before the capture row is marked deleted.
Storage failures leave the row eligible for a later retry and create an audit
event describing the failure without recording the storage key. Successful
deletion remains idempotent because already-deleted rows are excluded and
object-store deletes are safe to repeat.
