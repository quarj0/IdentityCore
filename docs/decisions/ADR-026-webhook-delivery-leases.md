# ADR-026: Claim webhook deliveries without locking producers during HTTP

## Status

Accepted

## Context

Webhook outbox producers lock endpoints to coordinate with explicit disablement.
Holding the same endpoint lock across outbound HTTP makes verification mutations
wait on a receiver. Event-first delivery locks also conflict with endpoint-first
administrative lock order. Retries must not revive cancelled events or allow a
late failed worker to replace a successful delivery.

## Decision

Use short endpoint-first/event-second transactions to claim and finalize delivery.
Persist a random claim and its expiry on the event, then release both row locks
before contacting the receiver. The lease lasts twice the configured HTTP timeout
plus 60 seconds. Only its current owner can finalize the event; expired claims
can be reclaimed by a later worker. Due-event selection excludes live claims.

Finalization checks the current event and endpoint states under the same lock
order. Disabled endpoints cancel pending events; failed endpoints pause delivery.
Replay clears any stale claim and atomically requeues the failed event with
endpoint reactivation. Stable event IDs and transport attempt history remain.

Write delivery audit events after releasing endpoint/event locks so the audit
chain lock does not invert the producer lock order. Audit failure is surfaced to
the worker; the delivery outcome and attempt record remain committed.

## Consequences

Database mutation latency is independent of the receiver timeout. Worker loss
remains recoverable. A crash after receiver acceptance or a request exceeding
its lease can cause duplicate HTTP delivery; receivers must atomically deduplicate
stable event IDs. Delivery ordering is not guaranteed. An additive migration adds
claim fields without changing the public event payload or API schemas.

## Validation

Regression tests cover network execution outside a transaction, duplicate-worker
exclusion, expiry recovery, late failure after a reclaimed success, explicit
cancellation, missing signing keys, and replay. Existing backend and migration
checks remain merge requirements.
