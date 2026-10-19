# Raw evidence report retirement

JSON/PDF verification reports contain profile, contact and extracted-document data.
They follow the snapshotted `media_retention_days` deadline from completion, alongside
raw captures. Retained verification outcomes, audit facts and metadata have their
separate policies; this worker does not erase those records. Active tenant-wide or
verification-specific legal holds defer deletion. A hold admitted after an external
delete begins cannot recall bytes already removed; use the audited hold command
before the deadline and follow the legal retention procedure.

Apply additive `verifications.0026` with the owning tenant keyring available. It
backfills an indexed deadline from the recorded completion time and valid immutable
policy, without inventing missing timestamps or interpreting malformed policies.
Revocation/cancellation must remain available during a tenant-key outage: an unreadable
policy leaves the deadline unset. The worker retries bounded, fairly ordered deadline
repairs after key recovery; no destructive work uses an unconfirmed policy. Investigate
terminal records with a persistently missing cleanup deadline before production.
Trusted SQL/bulk changes to completion or policy bypass model saves and must maintain
the deadline explicitly; public lifecycle paths update it through normal saves.

Before enabling retirement, drain and replace all old web/report-generation and
worker processes: older binaries ignore retirement markers and may recreate reports.
Keep the normal release-evidence, migration and protected review gates. The existing
retention schedule invokes `cleanup_retained_media_task`; its limit now selects only
due, unfinished cases and prioritizes unattempted cases then the oldest attempt.
Completed cleanup leaves the queue; failed objects retain their references and rotate
fairly. A missing media/evidence bucket or failed delete cannot count as success.

Report generation tracks both intended object keys before external writes. A partial
write remains known; a storage-route replacement retains old references for cleanup.
Deletion marks reports retired before I/O, removes each pointer only after successful
delete, and keeps failed references for retry. The service validates the exact case,
tenant/environment and retained route before deleting. Storage calls run outside the
short state transactions. Retired/expired report endpoints return 404, download links
are suppressed and ordinary generation cannot recreate them. Existing issued storage
grants remain bounded by their original expiry and object deletion.

Subject deletion preserves opaque report references, encryption flags and cleanup
state while clearing personal metadata. A late generation completion rechecks the
current state and re-enrols its known keys for retirement if needed. This is not an
atomic transaction with object storage: a crash or ambiguous response, including a
late external write interrupted before its final state check, still requires storage
inventory reconciliation against live references and approved retained routes. Do
not claim all orphan objects have been proved absent. Unmatched legacy reports whose
pointers were lost before this fix require authorized reconciliation; never infer
foreign ownership from a filename or blanket-delete shared buckets.

Inspect bounded `retention.evidence_report_deletion_failed` events and incomplete
cleanup/deadline-repair progress. Logs/audit events omit report keys and content. Restore storage/key
availability or repair a validated reference through controlled maintenance, then
rerun the ordinary worker. Do not clear pointers or mark cleanup complete to hide a
failure. Complete isolated crash/retry/hold/route drills and legal-policy acceptance
before production.
