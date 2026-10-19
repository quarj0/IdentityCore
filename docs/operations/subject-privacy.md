# Subject privacy requests

Subject export creation and confirmed deletion require the explicit tenant
`manage_subject_privacy` role permission. Membership and platform-administrator status
alone do not grant it. The additive access-control migration grants only designated
system Tenant/Organization Administrator roles; custom privacy roles require an
explicit authorized grant. Onboarding and DEBUG local seeding provision the designated
administrator grant. Apply migrations before using the updated UI/API, and verify
custom-role assignments through the normal authorized access process.

Deletion rechecks the actor's current grant inside the transaction. An active
verification-specific or tenant-wide legal hold defers anonymization. Associated
invalid legacy holds also block it pending authorized repair. Processing finalizers
and deletion take the tenant audit chain before case rows, avoiding inverted locks.

When permitted, deletion revokes live sessions, exhausts queued/running jobs and
cancels unfinished verifications. Completed outcomes remain retained. A cancellation
callback uses the opaque verification ID and an empty external reference; no subject
notification is queued by this path. Current consent checks reject deleted subjects,
and session authentication rejects them independently. A late worker cannot commit
new provider/document results after deletion. Already disclosed external requests
cannot be recalled; external processor deletion requires separate accountable action.

The transaction clears the profile, document fields, verification external references
and personal metadata, decision inputs, provider response/normalized copies and
previous subject-export payloads/tokens. Encrypted fields are saved with their owning
instances, preserving tenant/environment encryption. Export creation reloads and
locks the current subject so a cached pre-deletion object cannot recreate its data.
Audit facts, stable identifiers, retained outcomes and media subject to legal
retention remain; this is pseudonymization, not guaranteed erasure of every copy.

Opaque JSON/PDF report pointers remain tracked instead of being discarded during
metadata anonymization. Report-object retirement follows the raw-evidence deadline with legal-hold checks,
validated references and durable retry/progress state. See
[evidence report retention](evidence-report-retention.md). Do not claim complete
data-subject erasure or treat the implementation as privacy certification. Backups, exports already downloaded, logs,
external processors and applicable legal schedules require controlled procedures.

The service permits actor-free calls only for trusted internal maintenance; HTTP
routes always supply an authenticated, permission-checked actor. Run privacy tests
with synthetic data and include PostgreSQL finalization/fingerprint races before
rollout. The operation needs the tenant encryption keyring for encrypted-field saves;
a failed transaction does not establish successful deletion.


## Subject notification cleanup

Apply the additive notification subject-binding migration before deploying the new
producers/workers. Drain and replace every old delivery worker before enabling
this deletion protocol; old binaries lack the fresh-result guard. Preserve the
normal rollout/release gates. New applicant notifications bind their subject; model validation
rejects a mismatched tenant or non-subject recipient type. Deletion scrubs bound
messages and unbound legacy subject messages matched by the subject's current email
or phone, within the tenant. Messages bound to another subject remain untouched,
even when contacts are shared. Recipients become the non-deliverable `deleted`
marker; previews, encrypted delivery data and provider references are cleared.
Pending/failed messages become cancelled. Previously sent status/time and opaque
binding remain as delivery facts. No notification-row purge is claimed.

Delivery reloads current status and subject at admission and again before recording
its result, with short tenant-serialized transactions. Provider I/O runs outside SQL.
An already admitted send may reach its external processor during deletion and cannot
be recalled. Its late result cannot restore cleared references, message content or
recipient data. A queued/stale request after deletion does not send. External
mailboxes, SMS devices and processor retention require separate deletion procedures.

The migration adds a nullable binding without guessing legacy ownership. Historical
unbound rows with changed/unknown contacts, including subjects erased before this
rollout, require authorized reconciliation against an independently established
mapping. Do not assign shared addresses to guessed subjects or erase unrelated
recipient records. This limitation must be accounted for in deployment privacy
acceptance; it is not evidence of complete historical erasure.
