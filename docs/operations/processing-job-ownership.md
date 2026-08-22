# Processing job ownership invariants

IdentityCore processing workers use a durable `ProcessingJob` lease and acquisition generation (`attempt_count`) to prevent stale workers from committing evidence after a retry or recovery worker has taken ownership.

## Required invariants

- Lifecycle transactions that need both rows lock `Verification` first and `ProcessingJob` second. This order is shared by finalization, route exhaustion, completion, and stale-job handling to avoid lock inversion.
- A worker may persist successful provider results or domain evidence only while its exact `ProcessingJob` generation is still `processing` and locked.
- `ProcessingJobOwnershipLost` is a control-flow signal, not a provider failure. It must escape worker error handling without writing replacement success or failure evidence.
- A recovery-only acquisition after the normal attempt budget may finalize already committed provider evidence, but it must not invoke a provider again. Every biometric stage that participates in that recovery must therefore have reusable completed `ProviderCheck` evidence before recovery grace is granted.
- Resolved biometric rows do not trigger another provider call, but they still require durable reusable provider evidence before max-attempt recovery grace is granted. Workflows without a face-match stage require only reusable liveness evidence.

## Regression gate

Changes to processing ownership or provider-result persistence must run the processing-job, provider-route ownership, biometric finalization recovery, identity-document task, and full Django backend suites. CI and Security must be green on the exact pull-request head before merge.
