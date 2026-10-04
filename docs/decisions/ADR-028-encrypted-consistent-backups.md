# ADR-028: Encrypted, quiesced backup sets and isolated restore

Status: Accepted

Capture PostgreSQL custom-format dumps and all configured object buckets as one
client-encrypted backup set. Require paired deployment-specific quiesce/resume
hooks, resume even after a partially failed quiesce, and publish a success marker
only after the complete encrypted archive. Hooks must drain API/workers, block
external storage writers and retention, and undo those controls on resume.
This is an explicit pilot tradeoff: a short maintenance window buys consistent
snapshots while bucket versioning and online backup orchestration mature.

AES-256-GCM encrypts streams with independent random 96-bit nonces. Each member
is authenticated to its random backup ID and opaque archive filename. The
manifest, object names/headers, object checksums and database metadata are all
encrypted. No plaintext database dump is staged at backup. Restore authenticates
all files before mutation, uses a private temporary directory, then restores into
an empty isolated database and separate empty buckets. It verifies reference
sets, object digests, and tenant access through a retained synthetic drill.

The backup key is a separate owner-only secret file, never derived from application
keys or stored in the archive. Application/media key versions are escrowed in the
approved secret manager separately. Archive storage uses separate credentials,
server-side encryption, retention and access controls. Restored production runtime
storage overrides are ignored in isolated mode, preventing accidental source
storage access. External egress and worker startup remain blocked during drills.

Initial targets match deployment.md: RPO 24 hours and RTO 4 hours. Run backups
twice daily, monitor failure/freshness, and perform restore drills after relevant
changes and at least monthly. Tiny synthetic timings establish functional
correctness, not production-scale capacity or production key-grant readiness.
