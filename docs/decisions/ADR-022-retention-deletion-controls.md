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


Raw JSON/PDF report objects contain profile/contact/OCR data and share the snapshotted
media deadline. Indexed due/attempt/completion fields keep finished cases out of the
queue and rotate failed attempts. Retired reports cannot be regenerated through
ordinary API access. Object pointers remain until successful deletion; unknown
legacy deadlines/references require controlled reconciliation. See the
[report retirement procedure](../operations/evidence-report-retention.md) for rollout,
holds, storage routing and crash/uncertain-I/O limits. Metadata/outcome/audit retention
remains separate; report retirement does not claim deletion of those records.
