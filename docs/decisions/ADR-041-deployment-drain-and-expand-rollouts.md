# ADR 041: Instance drain and expand-only deployment gates

Status: Accepted

## Context

A process being alive does not establish readiness, and replacing workers during provider or finalization work must preserve durable processing leases. Database rollback can destroy evidence required by in-flight work. Deployment automation needs a gate for old/new schema compatibility.

## Decision

Keep liveness separate from a readiness endpoint that checks database and broker access and an instance-local drain marker. Operators drain each instance through a management command; the command marks it unready, cancels consumers on one explicitly named worker, and waits for two consecutive empty active/reserved/scheduled snapshots, resetting confirmation when work is observed. It never kills jobs, clears leases, or broadcasts to every worker. Timeout or missing worker replies fails the deployment while preserving the drain marker. Resume removes the marker only after dependencies are healthy.

New processing-job acquisitions are blocked while the instance is draining; active generations retain their existing ownership checks and may finish. Processing rows remain recoverable by the existing stale-lease sweeper. Celery uses one-message prefetch; only durable document/biometric tasks use late acknowledgement and requeue on worker loss. Duplicate delivery remains governed by durable generation and outcome checks.

Schema promotion accepts unindexed non-relational nullable fields or fields with non-null scalar server defaults, new tables and non-unique concurrent indexes automatically. Destructive, data-moving, renaming, constraint and ambiguous operations block automated promotion and require a separate staged design. Expansion runs before new code; old/new code overlaps only on a compatible expanded schema. Rollback changes code without reversing committed schema or clearing in-flight state. Contraction happens in a later release after old code and queued payloads are absent.

## Consequences

The drain file is per instance and must be shared by API/worker containers that are drained together; separate instances require separate commands. Broker control replies are mandatory. An unacknowledged drain remains unavailable until investigated or resumed. Sensitive credentials, payloads and active-task arguments never appear in drain output. Backward compatibility is tested with old model writes against an expanded PostgreSQL table, and migration operation classification fails closed.
