# ADR 058: Governed evidence, reusable claims and provider operations

Status: implemented bounded v0.4 contract; final validation and
protected review/merge and deployment release gates still apply. The
[governed resource](../operations/governed-resources.md) and
[provider operation](../operations/provider-operations.md) runbooks define supported
behavior. Broader illustrative architecture is not an additional public contract.

## Context

The owner expanded the agreed scope on 2026-10-20 to include the four capabilities
previously deferred in the platform roadmap. Existing verification evidence,
decisions and provider adapters are retained and integrated. PR #434 merged the
separate documentation-only receipt closing the historical review audit #281.

## Decisions

- Evidence is an independently addressable tenant/project/subject resource with
  immutable versioned schemas, encrypted normalized payloads, integrity hashes,
  provenance, bounded lineage and explicit retention. It can refer to a verification
  or another authorized workload. Generalization does not remove purpose controls.
- A purpose authorization records the subject, project, purpose, allowed operations,
  validity and legal-basis evidence. Consent-based grants must reference the actual
  current proof; other declared bases require independent privacy approval. A grant
  is not a legal opinion. Revocation and subject deletion invalidate descendant use.
- Evidence and claim writes are append-only in meaning. Corrections create new
  records and explicit supersession links. Content is never silently overwritten.
  Legal holds defer destruction but do not grant continued processing or disclosure.
- Claims reference evidence and/or earlier claims. Versioned deterministic rules
  govern normalization and derivation; conflicts are explicit and cannot be
  resolved by an implicit highest-confidence rule. Reviewer resolution preserves
  alternatives and requires current authority with maker/checker separation.
- Claim reuse evaluates current purpose authorization, source availability, schema,
  freshness, expiry, revocation and conflict state at access time. Selective
  disclosure returns only requested permitted claims or derived predicates, with
  expiring audience-bound capabilities, redemption checks and audited access.
- Cross-resource mutations follow the existing tenant-audit-first lock order.
  Concurrent deletion, expiry, supersession and callback finalization cannot
  resurrect revoked content or produce a stale successful disclosure.
- Provider Contract v1 synchronous responses remain compatible. A separately
  negotiated operation contract adds durable pending operations, authenticated
  callbacks and bounded polling. Operation identity, provider/configuration,
  tenant/environment, capability, request fingerprint, deadline and lease bind
  every terminal result. Duplicate results are idempotent; conflicting, late,
  replayed or unowned results fail closed. No provider I/O occurs under SQL locks.
- Certification is versioned and scoped to the exact provider manifest/configuration,
  capability/contract and test suite. Machine conformance and independently approved
  assurance evidence are separate levels; expiry, revocation and config changes
  invalidate readiness. Fixture success cannot certify a real provider deployment.
- Python, JavaScript, Java and .NET Provider SDKs implement the same signed exact-wire
  protocol, normalized envelopes, async operations, retention/deletion handlers and
  capability negotiation. Shared language-neutral fixtures and real HTTP integration
  tests establish interoperability. These packages are separate from API client SDKs.

## Completion requirements

Public OpenAPI and all four API client SDKs must cover the new resources. Tests must
exercise foreign/unknown equivalence, environment/project/purpose isolation, current
permissions, immutable writes, schema abuse, lineage bounds, lifecycle propagation,
privacy export/deletion, legal holds, idempotency, real PostgreSQL races and signed
provider HTTP interoperability. Update operating procedures and capability claims
only as their implementations pass. Do not represent real-provider/device/model or
independent legal/security assurance as supplied by synthetic integration tests.

Local repository validation is recorded in the [extension receipt](../reviews/platform-capabilities-validation.md); protected review and deployment gates remain separate.
