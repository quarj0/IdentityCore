# ADR 050: Purpose-bound consent and withdrawal

Status: Accepted

Consent proof records freeze the verification purpose, environment, notice version and locale, notice hash, and approved evidence processing scope at acceptance. Acceptance and withdrawal serialize with case mutations and tenant audit writes. Proof fields cannot change after insertion; withdrawal is a one-way audited transition. Repeat acceptance is idempotent only for an active matching proof. Withdrawing a proof does not erase its immutable evidence of acceptance and does not silently restore consent on retry.

Processing must check an active matching proof at applicant submission, durable job execution and before provider transfer. Snapshot policies define document and biometric evidence scope; legacy accepted records receive an explicit compatibility projection onto their original verification context, without fabricating notice history. New proof creation uses the snapshotted notice. Withdrawal revokes processing sessions and cancels pending work; in-flight work rechecks before storing results. Already disclosed evidence cannot be recalled, and committed processing already authorized before withdrawal remains auditable.

The applicant can withdraw using their scoped session; authorized tenant privacy operations can record withdrawal when a session has expired. Neither route allows cross-tenant or cross-verification actions. Proof and withdrawal events expose bounded opaque identifiers and consent context, without notice contents, contact information or evidence bytes in logs.

Tests cover purpose, environment, version and locale snapshots, immutable proof, evidence scope, withdrawal, repeat requests, queued processing and isolation.
