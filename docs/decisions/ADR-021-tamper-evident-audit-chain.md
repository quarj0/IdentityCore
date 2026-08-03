# ADR-021: Protect the audit trail with a tenant hash chain

## Status

Accepted

## Decision

Audit events are append-only. Each event stores the previous event hash for
its tenant and a deterministic integrity hash over its security-relevant
fields. Application updates and deletes are rejected, while an explicit chain
verification function reports the first invalid event.

The migration backfills hashes for existing events in tenant order so the
integrity check covers historical audit data as well as new events.
