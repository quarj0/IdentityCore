# Incident evidence preservation

Owner: Security/privacy lead. Use with [incident response](incident-response.md).
Preserve only material needed to investigate the incident under an authorized
purpose; incident handling is not permission for unrestricted data collection.

1. Record incident ID, collector, UTC acquisition time, authority, scope, source
   environment/tenant, and source system/version. Begin with audit metadata,
   deployment references, provider check IDs, and redacted operational logs.
   Keep subject and object references inside the restricted evidence system.
2. If routine deletion could remove relevant evidence, have the authorized
   privacy owner approve a narrowly scoped preservation hold. The application
   supports tenant-wide and verification-specific `RetentionLegalHold` records
   as described in [ADR-022](../decisions/ADR-022-retention-deletion-controls.md).
   After recording approval in the restricted incident system, a production
   operator places a tenant-wide hold with
   `python manage.py manage_retention_hold --tenant <slug> --place --reason <incident-reference>`
   or adds `--verification <verification-public-id>` for the narrow scope. Add
   `--expires-at <timezone-aware-ISO-8601>` when approval has a fixed end. Confirm
   the returned hold ID and `retention.legal_hold_placed` audit event before
   resuming cleanup. Release it only after approval with
   `python manage.py manage_retention_hold --tenant <slug> --release <hold-id> --reason <authorization-reference>`;
   the command locks the tenant while changing the hold and records the release.
   The application cleanup workers honor these holds for both retained media
   and temporary uploads, including initiated, quarantined, and consumed uploads.
   Before acquisition, pause the affected cleanup schedule and have its operator
   confirm already-running deletion work has drained; a newly placed hold cannot
   reverse an object deletion already in flight. Verify the fix is deployed.
   Validate the deployed administrative procedure, expiry, and actual cleanup
   behavior; do not assume that a database hold also pauses object-store
   lifecycle rules, provider deletion, or backup expiration. Coordinate each
   affected system separately and record its acknowledgement.
3. Acquire a read-only snapshot or export using a least-privilege identity. Do
   not modify the original to sanitize it. Keep originals encrypted in the
   approved restricted evidence store, with audited access and immutability
   controls when available. Create separately labeled redacted working copies.
   Never download raw evidence into an issue, chat, developer checkout, CI
   artifact, or personal device. Record any unavoidable change to a live source.
4. Compute a SHA-256 digest of each acquired artifact inside the secure evidence
   environment. Record byte count, digest, acquisition tool/version, UTC time,
   storage reference, encryption/key reference, and collector in the manifest.
   Hash the acquired bytes, not a reserialized working copy. A matching digest
   proves copy integrity; it does not prove completeness or source authenticity.
5. Verify the tenant audit chain using the deployed equivalent of
   `apps.audit.services.verify_audit_chain(tenant_id=...)`, described in
   [ADR-021](../decisions/ADR-021-tamper-evident-audit-chain.md). Record the result
   and snapshot time. Preserve failures and missing intervals; do not repair or
   rewrite the chain to make an investigation pass. Restricted direct-database
   access can alter data, so compare independent infrastructure/provider records.
6. Record every custody transfer: sender, recipient, authorization, purpose,
   timestamp, source/destination reference, and hashes before/after. Verify
   encrypted transfer and recipient scope. Separate tenant evidence and enforce
   environment boundaries; mixed-tenant material requires explicit security
   approval and an access plan before collection.
7. The privacy owner sets the retention/review date and tracks notification or
   preservation obligations. Release holds only with recorded authorization and
   confirmation that dependent systems can resume their normal policy. Verify
   deletion of originals and working copies when their approved purpose ends;
   retain the minimal custody/deletion record permitted by policy. Record failed
   deletions and retry owners rather than marking them complete.

The incident record links the private manifest and access history. A public
postmortem uses sanitized aggregates and references approved for disclosure,
never raw object keys, signed URLs, tokens, documents, or biometric payloads.
