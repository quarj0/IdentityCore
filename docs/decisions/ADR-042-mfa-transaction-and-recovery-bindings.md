# ADR 042: Locked MFA transactions and keyed recovery digests

Status: Accepted

MFA challenge payloads must never carry password hashes. Version-two signed transactions carry a keyed binding to the current password and revocation epoch. Enrollment rejects completed factors under a user lock. Verification consumes the factor and transaction atomically; TOTP steps are single-use, and live consumed transactions are retained until expiry instead of being evicted by later logins. Password-verified transactions share a user throttle bucket; unsigned guesses share the trusted peer bucket.

New recovery codes contain 128 random bits. Stored digests wrap the former per-user digest with a dedicated secret pepper and purpose separation. The `v2$` marker plus 61 hexadecimal characters fits the existing 64-character field and retains 244 bits of MAC output. The marker distinguishes protected rows from legacy rows without adding a schema field. Explicit pepper fallbacks preserve recovery across key rotation.

An idempotent data migration wraps existing digests without requiring plaintext codes. Conditional updates avoid double wrapping when a login or migration upgrades the same row concurrently. New writes already carry the marker and are excluded. Successful authentication also upgrades remaining legacy rows defensively. The migration is irreversible because old digests cannot be recovered from keyed wrappers.

This security format change requires a staged authentication cutover: drain old authentication instances before exposing the new format. Pending version-one transactions must restart password login. Application rollback retains the version-two authentication component and pepper keys; it must not restore a binary that cannot verify protected recovery rows. The expand-only rollout gate intentionally blocks this data migration until the staged security design has been applied. Durable verification/provider jobs do not change their payload or evidence format.
