# Purpose-bound consent and withdrawal

Consent acceptance stores an encrypted, immutable proof of the tenant, verification, subject, purpose, environment, archived notice version, locale, SHA-256 content hash, evidence scope and original acceptance timestamp. Document and biometric processing each require their corresponding scope. Frozen policy translations determine the notice shown to the applicant. Changing the purpose or environment requires new acceptance; an old proof cannot authorize the new context.

## Rollout and legacy records

Apply the additive consent migration before deploying the new application. Drain and replace all old workers before enabling processing: old binaries do not enforce the withdrawal gate. Existing records without a proof fail closed. Do not automatically infer original notice versions or permission scopes from today's templates.

Review archived notices and original case context before binding legacy records. Process only a reviewed tenant batch sharing the specified notice version and scope:

```sh
python backend/django/manage.py bind_legacy_consent --tenant TENANT_ID --notice-version 4 --evidence-scope document biometrics --batch-size 100 --after-pk 0
```

Resume using the returned primary-key cursor, with batches at most 1,000. The command preserves the acceptance timestamp, locale and notice text, rejects a nonempty mismatched hash, and marks the proof `legacy-reviewed`. This records an operator-reviewed binding rather than claiming that the proof existed at original acceptance. Audit metadata contains counts, cursors, version and scope, never notice text or subject data. Keep unreviewed or ambiguous records blocked and request new consent instead.

## Withdrawal

An applicant's current session bearer can POST the URL named `verification-session-consent-withdraw` (`/api/v1/sessions/{session_id}/consent/withdraw`) with an empty object. It binds withdrawal to that session's verification. The token is revoked by the successful withdrawal; subsequent requests with it are rejected.

Tenant privacy administrators require the explicit `manage_consent` permission to read acceptance records or POST `/api/v1/consent/records/{record_id}/withdraw`. Provision that permission on the appropriate existing production roles; local development seeding grants it to the Organization Administrator. Platform administrator status grants no implicit access. Tenant administrator withdrawal is idempotent.

Withdrawal atomically marks all accepted proofs for the verification, revokes its sessions, exhausts queued or running processing jobs, cancels a nonterminal verification and emits its cancellation callback. It retains the original proof and any completed final outcome. Audit events contain verification identifiers and environment only. Repeated withdrawal does not create duplicate cancellation or withdrawal events.

Provider dispatch and result commit both recheck current consent while holding the same tenant/case locks used by withdrawal. An already transferred external request cannot be recalled; its late result cannot become a new persisted processing result or decision after withdrawal. Pending retries cannot dispatch again. Withdrawal also excludes the verification from future reuse candidate comparisons.

Missing or unreadable acceptance proofs block processing. Recording the withdrawal timestamp does not require decrypting the proof, so customer-key unavailability does not prevent revocation. Key retention, legal retention and erasure policies still govern held evidence; withdrawal itself does not erase historical acceptance or retained evidence.

## Historical locale reporting

The consent history API returns `consent_locale: null` with
`consent_locale_status: "unavailable_legacy"` for the unsigned, unhashed English
default introduced for old rows by migration 0002. That default does not establish
the language shown to the subject. Current template language and content are
mutable and must not be used to reconstruct an old acceptance.

An explicitly stored non-default locale, a retained notice fingerprint, or an
available acceptance proof preserves the recorded locale with status `recorded`.
This status describes retained locale metadata; it does not validate the proof or
authorize processing. The normal consent-proof checks still apply. This reporting
change leaves stored locale defaults, notice snapshots, hashes, proof envelopes,
withdrawal timestamps and retained deleted records unchanged. Any future repair
of historical data requires independent evidence of the original notice locale.

Upload storage uses audited admission and a fresh-consent receipt commit without
holding SQL locks over external I/O. Withdrawal may complete during an admitted
write; the late candidate is rejected and receives best-effort cleanup. See
[upload transfers](upload-transfers.md) for recovery and retention requirements.
