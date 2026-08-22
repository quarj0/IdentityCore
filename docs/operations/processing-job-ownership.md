# Processing job ownership invariants

IdentityCore processing workers use a durable `ProcessingJob` lease and acquisition generation (`attempt_count`) to prevent stale workers from committing evidence after a retry or recovery worker has taken ownership.

## Required invariants

- Lifecycle transactions that need both rows lock `Verification` first and `ProcessingJob` second. This order is shared by finalization, route exhaustion, completion, and stale-job handling to avoid lock inversion.
- A worker may persist successful provider results or domain evidence only while its exact `ProcessingJob` generation is still `processing` and locked.
- `ProcessingJobOwnershipLost` is a control-flow signal, not a provider failure. It must escape worker error handling without writing replacement success or failure evidence.
- A recovery-only acquisition after the normal attempt budget may finalize already committed provider evidence, but it must not invoke a provider again. Every biometric stage that remains pending must therefore have a reusable completed `ProviderCheck` before recovery grace is granted.
- Already resolved biometric stages do not require another provider result, and workflows without a face-match stage remain eligible for finalization-only recovery when liveness evidence is reusable.

## Regression gate

Changes to processing ownership or provider-result persistence must run the processing-job, provider-route ownership, biometric finalization recovery, and identity-document task suites. CI and Security must be green on the exact pull-request head before merge.
