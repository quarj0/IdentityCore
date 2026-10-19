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
metadata anonymization. Report-object retention deletion and subject notification
recipient/delivery cleanup are separate outstanding remediation work until their
protected changes merge. Do not claim complete data-subject erasure or deploy this
partial stack as privacy certification. Backups, exports already downloaded, logs,
external processors and applicable legal schedules require controlled procedures.

The service permits actor-free calls only for trusted internal maintenance; HTTP
routes always supply an authenticated, permission-checked actor. Run privacy tests
with synthetic data and include PostgreSQL finalization/fingerprint races before
rollout. The operation needs the tenant encryption keyring for encrypted-field saves;
a failed transaction does not establish successful deletion.
