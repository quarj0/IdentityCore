# ADR 057: Short upload transactions and fresh consent at acceptance

Status: Accepted

Multipart parsing, bounded content reads, hashing, media inspection and object-storage
GET/PUT/DELETE run outside database transactions. Short admission and finalization
transactions acquire tenant audit, verification, session and upload locks in that
order. Both require current purpose-bound consent, session action, active case and
unexpired upload. Admission records `upload.transfer_admitted` with the opaque
operation, consent record and upload identifiers and purpose; it does not record
media, checksum or object key. Parsing the incoming multipart body precedes admission;
reading its accepted file content and transferring to storage follow admission.

Before PUT, validation rechecks consent and state. Each attempt writes to its own
`.validated.<operation>` candidate. Finalization checks consent and state again and
atomically stores the candidate key, checksum and signed receipt. Withdrawal can
commit during external I/O; a late write cannot become accepted evidence after it.
An admitted external request may still finish, and its temporary bytes cannot be
recalled synchronously. Rejected and losing candidates receive best-effort deletion.
Same-content retries retain the accepted key and receipt, including consumed or
promoted uploads; a losing concurrent attempt cannot delete the winner's object.

A failed database commit acknowledgement is ambiguous. The service logs only opaque
upload/operation identifiers and retains the candidate rather than risk deleting an
accepted object. There is no durable per-attempt recovery table. Operators must
reconcile unreferenced candidates with live upload/evidence references and configure
retention appropriate to the temporary bucket before production. Blindly expiring all
validated objects could destroy accepted retained evidence. See the
[operational procedure](../operations/upload-transfers.md).

This refines ADR 014 and ADR 050: SQL locks serialize acceptance with withdrawal,
not external storage latency. Legacy direct-object completion performs its bounded
read outside SQL and uses the same validation/receipt gate. Newly created uploads
expose the consent-aware API transfer, without a competing writable direct PUT.
PostgreSQL barrier tests cover withdrawal during PUT and two identical concurrent
transfers; transaction-level API tests cover multipart, scanner, storage and cleanup.

## Legacy direct PUT cleanup

Finalization journals the owned original temporary key in the same transaction as
its immutable receipt, for both `/transfer` fallback and legacy `/complete`.
Only the winning candidate starts best-effort source deletion. Storage I/O runs
outside SQL transactions; a storage failure preserves the accepted receipt and
cleanup reference. The existing upload retention worker retries these references,
including promoted and already-deleted rows, without counting them as newly
expired uploads. Attempts rotate so an unavailable oldest object does not starve
later references; active tenant/case holds defer deletion.

An immediate successful deletion retains its reference until upload expiry plus a
five-minute write grace period. An already-issued legacy PUT can recreate the old
object during its validity window. Migration `uploads.0007` recovers only generated
original keys from recognized validated-key suffixes; arbitrary historical keys
are not inferred. Runtime deletion still verifies case, tenant, environment and
retained route. The portal BFF accepts the narrow legacy `/complete` operation.

Apply the additive migration before deploying and drain old web/worker processes.
Stop issuing old direct grants; configure storage request timeouts and reconcile
legacy inventory after outstanding writes have quiesced. A paused external write,
ambiguous commit or crash can outlive the grace period: this is retryable owned
cleanup, not a distributed transaction or a zero-orphan guarantee. Unknown legacy
references, object versions and backups require deployment storage reconciliation.
