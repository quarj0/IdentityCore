# ADR-029: Preserve human decisions and bound bearer authentication cost

## Status

Accepted

## Context

The operational load drill found that automatic manual-review routing prevented
human decisions, late workers could replace decision evidence, joined row locks
blocked unrelated tenant traffic, and concurrent audit appends forked the chain.
Repeated expensive password verification also consumed the pilot CPU budget.

## Decision

Serialize decision writes on the verification row, with a persisted optimistic
revision. Reject stale revisions and automatic/system writes over human proposals or
terminal outcomes before changing risk or decision records, and audit the
conflict. Human review replaces an automatic or system nonterminal review route while
retaining its evidence in the encrypted decision summary. Independent approval
locks the verification before its decision and advances the revision.

Lock only the verification being changed, without its joined tenant or subject.
Use PostgreSQL NO KEY UPDATE where state changes do not alter keys, allowing
unrelated foreign-key validation to proceed. Serialize audit appends on the
tenant with the same non-key lock. Webhook producers and endpoint actions take
that audit lock before endpoint locks; delivery releases its locks before audit
work. Audit appends stay inside the domain transaction.

Server-generated session tokens and API-client secrets contain 256 random bits. Store their SHA-256
digests with a distinct version prefix and compare in constant time. Only
explicit callers of the server credential generators opt into this format; user
passwords and existing session hashes retain password hashing. No migration of
live sessions is needed.

For legacy session hashes and API-client password hashes, retain at most 2,048
successful verification proofs per process for five minutes. Proof keys are
HMAC digests under a random ephemeral process key, binding the presented token
to the current encoded database hash. Never cache failures or raw credentials.
Every request still reads the database and enforces current credential hashes,
rotation overlap expiry, session expiry/status, client status, allowed IPs,
permissions, environment and quotas. Restart drops proofs; cache eviction falls
back to the original password check.

## Validation and consequences

Real PostgreSQL tests race human final and pending decisions against stale
workers and append 80 audit events concurrently. Authentication regressions
cover invalid proofs, bounded eviction, expiry, rotation and revocation after
warming a proof, plus new and legacy token formats. The operational drill checks
tenant isolation, human outcomes, audit integrity and drained processing/outbox
work. Provider inference and production storage capacity require a separate
deployment-specific measurement.
