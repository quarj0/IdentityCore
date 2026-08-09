# Provider Runtime

## Status

Implemented foundation with planned expansion.

## Purpose

The Provider Runtime is IdentityCore's vendor-neutral execution boundary. It allows a
workflow to request a capability without coupling the workflow, policy, or decision
domains to a particular vendor, model, registry, or deployment.

The runtime is used for IdentityCore Managed Providers and is intended to be the same
boundary used for commercial, government, and customer-hosted providers.

```text
Workflow Engine
      |
      v
Provider Runtime
      |
      +--> IdentityCore Managed Provider
      +--> Commercial provider
      +--> Government registry
      +--> Customer-hosted provider
      +--> Supporting infrastructure provider
```

## Responsibilities

For each capability invocation, the runtime should:

1. Resolve tenant, project, environment, workflow, and policy context.
2. Determine the required capability and contract version.
3. Resolve the selected provider and adapter.
4. Validate that the provider supports the capability and input context.
5. Create an auditable provider check or attempt.
6. Build a minimal request containing only authorized evidence and context.
7. Apply authentication, signing, timestamp, nonce, and idempotency controls.
8. Enforce endpoint, egress, timeout, response-size, and content restrictions.
9. Invoke the provider.
10. Validate and normalize its response.
11. Persist a versioned result, duration, status, and redacted diagnostics.
12. Return deterministic success or failure semantics to the workflow.
13. Trigger retry, fallback, more evidence, or Manual Review according to policy.

## Runtime boundary

Core business logic must not call a provider client directly. It should request a
capability from the runtime.

This boundary ensures that:

- applications do not change when providers change;
- workflows remain provider-neutral;
- provider failures have consistent semantics;
- credentials and endpoints remain outside domain logic;
- results are normalized into IdentityCore evidence;
- every invocation is attributable and auditable.

## Provider types

### IdentityCore Managed Providers

IdentityCore-operated implementations currently include selected document quality,
document classification, OCR, face comparison, liveness, and presentation-attack
capabilities. The FastAPI AI service hosts these implementations.

Managed Providers are defaults, not privileged architectural paths. They must conform to
the same capability, evidence, failure, versioning, and audit rules expected of external
providers.

### Commercial providers

Commercial IDV, OCR, biometrics, authenticity, fraud, watchlist, risk, and data providers
can participate through adapters or the secure HTTP provider contract.

### Government and authoritative providers

Authorized registries can implement identity lookup, credential validation, issuer
verification, eligibility, or other authoritative capabilities.

### Customer-hosted providers

A customer may operate a capability in its own network, private cloud, or data center.
IdentityCore still governs contract validation, signing, invocation records, evidence
normalization, and failure behavior.

### Infrastructure providers

Storage, key-management, messaging, and related infrastructure are also provider
categories. Some are architectural directions rather than complete runtime capabilities
today.

## Provider records and assignments

Provider configuration is scoped to platform or tenant context and may include:

- provider identity and adapter type;
- ownership: managed, platform, or tenant;
- capabilities;
- encrypted configuration and credential references;
- endpoint and signing configuration;
- environment availability;
- country and document support;
- health and operational status;
- residency, retention, and data-processing metadata.

A provider assignment associates a capability with a selected provider for an allowed
scope. Assignments remain the compatibility fallback when no conditional route matches.

The current implementation also includes tenant-owned, environment-scoped provider
routes. Each immutable published route version declares one capability, optional country,
document-type, and workflow conditions, and an ordered provider chain. Publishing a newer
version retires the previous active version with the same route key. A provider check
records the selected route public ID, version, and chain position in safe request metadata
so later execution and audit work can explain the selection.

Route selection is deterministic. Matching routes are ordered by:

1. the number of configured condition dimensions, most specific first;
2. numeric priority, lowest first;
3. route key, lexicographically;
4. version, highest first; and
5. public ID as a final stable tie-breaker.

An empty condition list is a wildcard for that dimension. Only active providers belonging
to the tenant or defined as platform providers can be returned. If no published route
matches, the runtime uses the active tenant assignment and then the managed system default.

## Invocation lifecycle

### 1. Resolve

The runtime resolves the capability and provider from tenant, environment, workflow, and
policy context. Resolution must fail closed when the provider is disabled, unavailable,
not assigned, or incompatible.

### 2. Prepare

The runtime creates a provider-check record before or atomically with execution. Requests
must contain only the minimum evidence and metadata required by the capability contract.

Evidence should be supplied through short-lived grants or signed references where
possible rather than copied into long-lived provider configuration or logs.

### 3. Secure

Custom provider calls must apply controls appropriate to the contract:

- approved HTTPS endpoints;
- egress and SSRF protections;
- authentication or key identifiers;
- canonical request signing;
- timestamps and bounded clock skew;
- nonce and initiating-request binding;
- replay detection;
- idempotency keys;
- strict timeout and response-size limits;
- content-type and schema validation.

The repository includes a versioned HMAC signing protocol and deterministic fixture in
`provider-signing.md` and `docs/fixtures/provider-signing-v1.json`.

### 4. Invoke

The adapter translates the capability request into the provider's protocol. Adapters may
be in-process managed adapters or secure remote HTTP adapters.

### 5. Normalize

Vendor-specific output must be validated and transformed into a versioned IdentityCore
result. Normalization includes:

- stable status and reason codes;
- bounded scores and confidence;
- model/provider/adapter versions;
- structured evidence values;
- retryability and availability metadata;
- redaction of credentials, media locations, tokens, and personal data from telemetry.

A provider response is not automatically a final decision.

### 6. Record

The provider check records the selected provider, capability, status, start and completion
timestamps, duration, normalized result, safe request/response metadata, and failure
information.

Provider checks form part of evidence lineage and decision reproducibility.

### 7. Continue

The workflow receives a normalized result or deterministic failure. Policy determines
whether to:

- continue;
- ask the subject for another capture;
- retry the same provider;
- select a fallback provider;
- mark the capability unavailable;
- require Manual Review;
- stop the workload safely.

## Failure semantics

At minimum, the runtime should distinguish:

- `succeeded`;
- `failed`;
- `timeout`;
- `unavailable`;
- `malformed_response`;
- `unsupported`;
- `authentication_failed`;
- `signature_invalid`;
- `replay_rejected`;
- `policy_blocked`;
- `cancelled`.

Failures must not be converted into approval. Unsupported, inconclusive, or unavailable
results should follow explicit workflow and policy behavior.

## Retry and fallback

Retries and fallback must be policy-driven and auditable. A safe retry design accounts
for:

- whether the capability is idempotent;
- provider timeout and retry guidance;
- maximum attempts and backoff;
- operation expiry;
- evidence grant expiry;
- provider health and circuit state;
- whether retrying could duplicate a high-impact external action.

The repository implements ordered routes conditioned on capability, country, document
type, workflow, tenant, and sandbox or production environment. Each route defines a
bounded timeout, maximum attempts per provider, circuit threshold and recovery interval,
and terminal action. The executor retries only errors explicitly marked retryable, then
moves through the ordered provider chain. Every invocation and circuit skip creates a
provider check plus a correlated safe attempt record containing the route step, sequence,
outcome, safe error code, retryability, timeout, and fallback reason.

Circuit state belongs to an immutable route step. Consecutive retryable failures open the
circuit. Calls skip it until the recovery deadline, after which one caller atomically
claims a half-open probe; success closes the circuit and another retryable failure reopens
it. Exhausting the chain applies the route's explicit `manual_review` or `fail` action and
records only safe codes in decision and audit evidence. Cost-, latency-, and
residency-aware selection remain future work.

## Health telemetry

The runtime exposes redacted health snapshots for one tenant, environment, and bounded
time window. Each provider snapshot includes terminal attempt counts, availability and
error-rate percentages, p50/p95/maximum latency, capability names, and controlled error
codes. Active route snapshots include ordered provider steps and current circuit state so
operators can diagnose routing without access to credentials or provider configuration.

Tenant users request an explicit `sandbox` or `production` scope from
`GET /api/v1/providers/health/`; the default window is 24 hours and the supported range is
1 to 720 hours. Platform administrators can inspect the same data through
`platformProviderHealth`, but results remain separate tenant/environment groups rather
than a cross-tenant aggregate.

Health responses never include request, response, or normalized provider payloads; error
messages; configuration; credentials; subject fields; or evidence references. A check
without a project is treated as sandbox data for compatibility with pre-project records.
The current operational threshold marks a provider degraded when at least 5 percent of
terminal attempts in the selected window fail, and unavailable when none succeed.

## Tenant and environment isolation

Provider resolution, credentials, configuration, checks, evidence, and telemetry must be
scoped to the authenticated tenant and project environment.

Sandbox credentials must not execute production providers or access production evidence.
A provider owned by one tenant must not be discoverable or invokable by another tenant.
Background jobs must carry and validate the same scope as the initiating request.

## Privacy and evidence access

Provider invocation follows data minimization:

- provide only required evidence;
- prefer time-limited references over copies;
- avoid exposing unrelated claims or raw media;
- record the purpose and capability;
- prohibit secrets and evidence locations in logs;
- apply retention and deletion requirements to provider-derived evidence;
- disclose provider participation where required by consent or policy.

Future provider manifests should declare processing location, retention, subprocessors,
training use, and deletion behavior so policy can evaluate provider suitability.

## Observability

Safe runtime telemetry may include:

- request and correlation IDs;
- tenant/project/environment identifiers appropriate for internal operations;
- provider and capability IDs;
- adapter and schema versions;
- status, duration, retry count, and safe error code;
- redacted request/response metadata;
- route and fallback reasons;
- model version where relevant.

Telemetry must not include raw documents, selfies, biometric templates, provider secrets,
signed URLs, access tokens, or unmasked identity fields.

## Conformance

A production provider ecosystem requires automated conformance tests for:

- capability schema compatibility;
- canonical signing fixtures;
- replay rejection;
- timeout and retry behavior;
- malformed and oversized responses;
- score and confidence validation;
- sensitive-field redaction;
- evidence provenance;
- tenant and environment isolation;
- idempotency;
- declared retention and deletion behavior.

## Current implementation maturity

Implemented foundations include:

- provider registry and tenant assignments;
- provider adapter protocol and registry;
- managed AI capabilities routed through adapters;
- centralized invocation bookkeeping;
- normalized provider checks and versioned results;
- duration and failure recording;
- recursive telemetry redaction;
- secure custom HTTP provider calls;
- signed, timestamped, nonce-bound, replay-resistant provider messages.
- immutable conditional routes and deterministic provider-chain selection;
- per-route timeouts, bounded retries, ordered fallback, circuit recovery, and terminal
  Manual Review or failure actions;
- correlated attempt history with safe retry and fallback reasons.
- published Provider Contract v1 fixtures and a local signed HTTP conformance runner for
  success, malformed, timeout, replay, and version-negotiation behavior;
- CI checks for the fixture runner and every built-in adapter capability's Contract v1
  normalization boundary.

Continued work includes:

- provider manifests and broader capability, evidence, idempotency, retention, and
  deletion conformance coverage;
- organization self-service onboarding, testing, promotion, and credential rotation;
- first-class storage and KMS/HSM provider routing;
- broader registry and external risk adapters;
- production certification and operational runbooks.

## Related documentation

- [Canonical Architecture](../../ARCHITECTURE.md)
- [Capability Model](capability-model.md)
- [Evidence Model](evidence-model.md)
- [Claims Engine](claims-engine.md)
- [Provider Signing](provider-signing.md)
- [Provider Route Resilience](../operations/provider-route-resilience.md)
- [Product Alignment](product-alignment.md)
