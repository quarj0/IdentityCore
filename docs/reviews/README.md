# Historical review audit (#281)

Reconciled on 2026-10-20 against merged main
`0d3231a4f668bb312124a0852bc6445316cd1282`.

976 threads from closed or merged PRs: 470 fixed, 506 verified, 0 actionable and 0 pending individual audit. Reconciled against merged main 0d3231a4f668bb312124a0852bc6445316cd1282 after PR #433; resolution state is not implementation evidence.

The inventory covers all 329 closed or merged PRs returned by the repository API
at reconciliation time. PR and thread pagination were exhausted. The register
contains the same 976 original thread/comment pairs, without duplicates. This
extends the original 484-thread issue scope and the prior 860-entry register.

## What changed

[PR #433](https://github.com/quarj0/IdentityCore/pull/433) merged on 2026-10-20 at
09:40:30 UTC. Its merge tree is identical to independently reviewed final head
`26242408ab2a5861c27d1d26f96f90f357a1d16f`. The 120 findings previously marked
“actionable until protected merge” now cite that receipt and their implementation
or regression evidence. Their prior notes remain in `pre_merge_disposition_note`,
including deployment and assurance limits; completion does not remove those limits.

The live inventory found another 116 unregistered threads, including feedback on
consent, media inspection, SDK contracts/completion and the review gate. Each
original body was read and reconciled against current implementation and named
evidence. Of these, 113 are fixed and three verify the explicitly accepted mutable
review timing policy. Thread resolution alone was not used as proof. The live snapshot still contains
56 unresolved historical threads; their individual dispositions are recorded here.
No historical resolution flag was changed during this reconciliation, and #433
had no unresolved review thread at merge.

The unresolved historical response-authentication thread on closed PR #406 is
implemented in #433: bounded signed error bytes are authenticated before HTTP
status influences routing, with unsigned/replayed error and size-limit regressions.
Closing #406 did not establish this disposition; the merged code does.

Private vulnerability reporting was enabled by the administrator and verified via
repository API (`enabled: true`) on 2026-10-20. Normal-reporter navigation remains
a release checklist check, without sending a sample report. GitGuardian incident
38304031 was classified by the owner as a synthetic test credential; the check
passed. No scan exclusion was added to the repository.

## Validation and receipts

On the merged tree, the reconciliation reran:

- 149 focused backend tests: 148 passed, one PostgreSQL-only skip.
- Five consent-key recovery tests: all passed.
- 170 review-gate regressions: all passed.
- Eight provider conformance HTTP tests: all passed.
- Shared frontend API-client tests: passed, including binary refresh and failed logout.

The focused backend selection includes upload/media inspection, consent and its
historical artifacts, system decisions, historical review protocols, processing
evidence, signed transport, platform invitation delivery and organization review
finalization. PostgreSQL-only concurrency is supported by the already completed
239-check CI-base-settings run on the identical reviewed tree; the SQLite skip
above is not presented as a new PostgreSQL execution.

The reviewed final head also completed all required CI/Security checks, including
frontend, backend, migrations, AI, SDK and container jobs. The final configured
Codex review [completed without findings](https://github.com/quarj0/IdentityCore/pull/433#issuecomment-6272231840).
After administrator-scoped workflow approval, the dedicated App
[review gate passed](https://github.com/quarj0/IdentityCore/actions/runs/39400354775).
The owner then completed the documented trusted merge. This connection still
cannot read administrative branch-protection settings; no new independent API
verification of those settings is claimed here.

## Audit closure and future feedback

The historical code findings have evidence-backed dispositions and no pending or
actionable entry remains in this snapshot. Issue #281 can close after this
reconciliation is reviewed and recorded on main. The live issue remains open
until that receipt is published; this document does not claim it has been closed.

For subsequent PRs, inspect every thread, implement valid feedback, attach commit
and passing-check evidence, obtain fresh final-head review and use the trusted
merge tool. New feedback after this snapshot needs its own assessment. Retain
strict native CI/Security, the dedicated App binding and conversation protection.

## Remaining release boundary

This audit does not certify a deployment. Production configuration, real providers,
physical devices and assistive technologies, model/PAD performance, data migration
and reconciliation, external processor deletion, restore/paging/rollback drills,
independent security/privacy assessment and accountable go-live approval remain
release work. See the [product assessment](../architecture/product-alignment.md)
and [portal release gates](../operations/verification-portal-production.md).

Reusable claims, a generalized public evidence/lineage API, broader provider
certification and asynchronous provider contracts remain deferred platform
expansion. General verification-case escalation is also not implemented; the audit
corrects that capability claim rather than claiming a new escalation feature.

See the [frozen pre-merge worklog](history-through-2026-10-19.md) for historical
validation batches and former blockers. The disposition register is the current
per-finding record.
