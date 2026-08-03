# ADR-018: Version and persist decision inputs

## Status

Accepted

## Decision

Every automatic or manual decision stores a versioned decision contract,
stable reason-code list, and encrypted input snapshot. The snapshot includes
the immutable policy/workflow snapshots, risk signals, and normalized provider
check results required to reproduce the outcome.

Unknown or missing evidence remains represented in the snapshot and is handled
by the risk rules as a safe review or rejection outcome; it is never silently
treated as a successful check.
