# ADR-033: Durable environment API quotas

Status: Accepted

## Context

Process-local DRF rate counters can overspend under concurrency and expose no
organization-wide environment usage. API clients already have a per-minute limit.

## Decision

Reserve all organization minute/month and client minute limits in one PostgreSQL
transaction serialized on a dedicated tenant/environment quota row. Persist
admitted and denied counters without request/evidence payloads, expose explicit
response headers, and provide tenant-only dashboard aggregates. Keep sandbox and
production separate, use UTC calendar windows, and purge old counters after 90 days.

## Consequences

Counters survive worker restarts and failures cannot silently admit uncounted
traffic. A hot tenant/environment serializes reservations and requires measured
capacity planning. Dashboard/session traffic uses its existing independent
throttles; API-client GraphQL authentication is unsupported.
