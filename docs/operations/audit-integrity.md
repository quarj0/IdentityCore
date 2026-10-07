# Audit event integrity

Audit events are appended under the tenant row lock. The application assigns creation time and normalizes IPv6 before persistence. New version-2 hashes include the public ID. ORM bulk insertion, update and deletion are rejected; the admin exposes records for viewing only.

Each event additionally carries an HMAC authentication tag over its version, key ID, public ID, hash and canonical payload. A dedicated audit key is derived from the application keyring with domain separation. Retain historical application keys during rotation; an unknown key, missing tag or unsupported version fails verification. A database writer cannot create replacement authentication tags by recomputing the public SHA-256 chain.

Migration 0004 preserves version-1 timestamps, public IDs and original hashes. It validates the existing chain before authenticating each historical event; it aborts if an existing hash or predecessor is inconsistent. This establishes authentication from migration time and does not prove that older unsigned history was never rewritten.

Pause all audit-producing web processes and workers during deployment, take a database backup, apply the migration with the application keyring available, then start only the updated application version. Investigate a preflight failure before retrying; do not clear or rebuild historical hashes to bypass it. Older versions must not append unsigned events after this migration.

Authentication detects modifications to retained events. Detection of database rollback, whole-chain deletion or tail truncation requires an independently retained external checkpoint. The database chain alone does not establish that completeness guarantee.

## Platform administrator events

Tenantless administrator authentication and MFA events use the separate platform chain (`tenant_id=None`). Only an existing tenantless platform administrator may be its actor; tenant and system actors cannot append to this chain. PostgreSQL appends hold a dedicated transaction advisory lock. The same immutable, authenticated audit format verifies platform events, and tenant audit APIs cannot list or retrieve them.

Production must replace the AI service sample token. The current `.env.example` value is an explicit placeholder; startup also rejects the fingerprint of the previously published credential. Rotate that credential wherever older deployments copied it.
