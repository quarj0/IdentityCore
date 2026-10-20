# Upload transfer and temporary candidates

New uploads use the consent-aware multipart transfer endpoint. The legacy completion
endpoint validates a bounded stored object and copies it to a separate accepted
candidate; it does not bless a still-writable original object. Current consent and
session scope are required even for completed retries.

The service parses multipart outside SQL, checks declared size before reading file
chunks, records an audited admission, validates content, checks consent before PUT,
and rechecks it before accepting the checksum and signed receipt. Storage does not
hold SQL row locks. Withdrawal during an admitted write prevents acceptance, though
that external write may finish. Unsafe input can quarantine an initiated upload;
malformed retries cannot quarantine already accepted evidence.

Candidate keys have an opaque per-operation suffix. Failed or superseded attempts
are deleted best effort. A process crash, storage failure or uncertain database commit
can leave an unreferenced object. The `upload.transfer_admitted` event and bounded
cleanup/finalization warnings identify operations without logging bytes or keys.
Admission does not prove acceptance: inspect the current upload status, receipt and
stored key. No durable attempt/outbox or scheduled candidate reconciler is provided.

Before production, provision a reconciliation procedure that enumerates candidate
objects, checks references in the current database and retained evidence, excludes
in-flight requests with a conservative grace period and deletes only confirmed
unreferenced objects. Validate it in isolated storage with the application's approved
tenant/environment routing and retention/hold policies. Blanket expiry of validated
objects is unsafe because accepted uploads use those keys too. Track cleanup failures
and uncertain finalization warnings; do not retry deletion of an accepted key. These
storage/retention and real failure-drill checks remain deployment work.

See [ADR 057](../decisions/ADR-057-upload-transfer-transactions.md),
[capture provenance](capture-provenance.md) and
[purpose-bound consent](purpose-consent.md).

Legacy direct objects now have a separate cleanup journal (`original_storage_key`
and `original_cleanup_attempted_at`). Apply `uploads.0007` before deploying and drain
old web/worker processes. The migration recovers recognized generated original
references from validated keys, including already-deleted uploads; unknown legacy
references require storage inventory reconciliation. The upload retention worker
retries the owned original object outside SQL transactions, checks active holds,
and retains failed references. Immediate cleanup preserves the journal through
upload expiry plus five minutes, then sweeps again before clearing it. This covers
still-valid old PUT grants; configure request timeouts and reconcile storage after
old writes quiesce because a paused write or crash may outlive that grace period.
Object versions and backups need their own retention controls. Never delete all
`.validated` keys: accepted evidence uses them.
