# Provider assurance and asynchronous operations

Synchronous Provider Contract v1 remains supported. Async execution is separately
negotiated as `ic-provider-operations-v1`; an async response cannot silently change
a synchronous configuration. See [Provider SDK packages](../../provider-sdk/README.md)
and [governed resources](governed-resources.md).

## Scope and approve assurance

An authorized tenant user obtains the current report scope from
`GET /api/v1/providers/certifications/scope` with
`configuration_id` and `capability` in the query. Reports bind the exact configuration digest, manifest
hash, environment, capability, contract, operation contract and suite version.
Changing any bound configuration invalidates its readiness.

Propose a certification at `POST /api/v1/providers/certifications` with the scoped
report, every required case passed, the SHA-256 of retained test artifacts, level,
validity and deletion deadline. `conformance` records protocol evidence; `assured`
also requires independent assurance references. A different active tenant user
with both `manage_provider_assurance` and `approve_provider_assurance` must inspect
and approve it. The proposer cannot approve their own report. Listing, metadata
detail and explicit revocation are available under the same public resource.
Uploading assertions or approving a record does not commission or independently
issue an external certificate. Retain and verify the actual evidence separately.

`provider-assurance/v1` requires success, malformed input, timeout, replay,
version negotiation, capability/environment binding, deletion and redaction.
Async also requires pending, callback authentication, polling, duplicate and
conflicting completion, late completion, cancellation and lease binding. Shared
SDK tests exercise these cases in an isolated harness. Their artifacts are marked
synthetic and do not establish deployment-specific capability/model/deletion or
security assurance. Inspect and approve reports for the actual deployment scope.

## Configure and execute

Set `operation_contract=ic-provider-operations-v1`, `signing_mode=hmac_v1` and
`required_assurance=conformance` or `assured` on the environment configuration.
Test and independently activate it through the existing setup flow, then obtain
current assurance before assigning it to a route. Async operation timeout is
30–86400 seconds and polling interval is 5–300 seconds. The case's expiry further
bounds the deadline. Production uses its own approved configuration and secrets.

An existing durable processing job admits one operation for its provider check,
fingerprints the original inputs and persists an encrypted random lease. Start
and poll POST to the same approved HTTPS endpoint. Do not follow provider-returned
URLs. Input transfers happen only at the transport boundary. Network I/O runs
outside SQL locks. Admission ambiguity reconciles the same operation ID instead
of creating another job or selecting a fallback provider.

The immutable binding contains the operation contract, operation/configuration,
tenant, project, environment, capability, contract version, original request hash,
lease generation, deadline, callback path and opaque lease token. Providers must
echo the complete binding. A pending operation defers its worker without consuming
a processing attempt; terminal normalized results resume the original worker.
A provider pending state is not a completed check or a verification decision.

## Callbacks and cancellation

POST terminal results to the admitted `/providers/operations/{id}/callback` path
on the configured IdentityCore origin. Sign the exact bytes with the configured
HMAC key, fresh timestamp and nonce. IdentityCore revalidates the complete binding,
shared replay claim, current consent, project, tenant, provider/configuration,
assurance, deadline and durable job ownership before committing a result. Identical
terminal results are idempotent; conflicting, stale, late or unowned results fail
closed. The signed metadata-only receipt echoes the request nonce. Retry with a
fresh signature/nonce after an uncertain response. Never log the raw lease or result.

The metadata-only `GET /providers/operations` requires an exact `project_id` and
supports verification, status and capability filters. Detail and cancellation also
require the exact project. API credentials need `providers:operations`; users need
`manage_providers`. Cancellation immediately fences local use and durably queues
remote cancellation. It does not assert that the external job has stopped.

## Privacy maintenance and acknowledgments

The retention worker retries pending signed cancel/delete controls outside SQL
locks, every five minutes, for up to 30 days from the latest remote action request.
Provider acknowledgments must echo the complete binding and exact terminal control
status. Ambiguous or failed acknowledgments stay pending; exhausted ones are
explicitly expired. Inspect `remote_action`, `remote_action_status`, requested and
attempted timestamps on operation metadata. Escalate expired acknowledgments to
the accountable provider/privacy owner; do not represent them as successful erasure.

A held subject deletion cancels work while preserving content. Actual authorized
erasure queues remote deletion and scrubs platform result copies. Cancel retains
the raw lease for a later delete; successful delete or explicit retry exhaustion
clears it. Platform operation result copies expire one day after their original
deadline unless held. Certification report retention is separate from validity.
Use existing worker/beat health and incident procedures, and retain independent
processor deletion, backup and production assurance evidence.
