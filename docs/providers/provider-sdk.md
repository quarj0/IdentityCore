# IdentityCore Provider SDK

> Status: architecture and integration contract.
>
> This document describes how a provider integrates with the IdentityCore Provider Runtime. It is distinct from the customer-facing Python, Java, and .NET SDKs used to call IdentityCore APIs.

## 1. Purpose

The Provider SDK defines a stable integration boundary for any system that supplies an identity capability to IdentityCore.

A provider may be:

- an IdentityCore Managed Provider;
- a commercial identity verification vendor;
- a government or authoritative registry;
- a customer-hosted service;
- a risk or fraud engine;
- an object-storage provider;
- a KMS or HSM provider;
- a notification or supporting infrastructure service.

The goal is to let IdentityCore orchestrate providers without embedding provider-specific behavior in core workflow, policy, evidence, or decision code.

## 2. Provider contract

Every provider integration must define:

- provider identity and version;
- supported capabilities;
- supported contract versions;
- deployment mode;
- authentication method;
- input requirements;
- normalized output schema;
- failure and retry semantics;
- residency and retention declarations;
- health and readiness behavior;
- observability and redaction rules.

## 3. Provider manifest

A provider manifest describes what a provider can do before execution begins.

Example:

```json
{
  "provider_id": "example-document-provider",
  "display_name": "Example Document Provider",
  "version": "1.4.0",
  "deployment_mode": "remote_http",
  "capabilities": [
    {
      "id": "document.ocr",
      "versions": ["1.0"],
      "countries": ["GH", "NG", "KE"],
      "document_types": ["passport", "national_id"]
    }
  ],
  "residency": {
    "regions": ["africa-west"],
    "cross_border_processing": false
  },
  "retention": {
    "stores_input_media": false,
    "maximum_retention_hours": 0
  }
}
```

A future machine-readable manifest format should be versioned independently of provider implementation versions.

## 4. Capability declaration

Capabilities use stable IDs defined by the IdentityCore capability model.

Examples:

```text
document.quality
document.classification
document.ocr
document.authenticity
biometric.face-match
biometric.liveness
identity.registry-lookup
risk.assessment
storage.object
key-management
notification.delivery
```

A provider may implement one or many capabilities. IdentityCore must resolve compatibility before invocation.

## 5. Invocation envelope

A provider invocation should include a versioned envelope independent of the capability payload.

```json
{
  "contract_version": "1.0",
  "request_id": "req_...",
  "invocation_id": "pinv_...",
  "capability": "document.ocr",
  "capability_version": "1.0",
  "tenant_context": {
    "project_id": "prj_...",
    "environment": "sandbox"
  },
  "evidence": [],
  "parameters": {},
  "callback": null
}
```

The envelope should not expose internal database identifiers, unrelated tenant information, or unnecessary subject attributes.

## 6. Evidence access

Providers should receive the minimum evidence necessary for a capability.

Preferred access methods:

- short-lived signed object URLs;
- one-time evidence grants;
- encrypted request payloads for small structured evidence;
- private network access for customer-hosted deployments;
- storage references when data should remain in the customer's boundary.

Evidence grants should be:

- capability-scoped;
- provider-scoped;
- short-lived;
- auditable;
- revocable where possible;
- unusable across tenants or environments.

Raw biometric templates must not be exposed unless the capability contract explicitly requires them and deployment policy permits it.

## 7. Authentication and message integrity

Remote providers must support an approved authentication mechanism.

Possible mechanisms include:

- HMAC signatures;
- asymmetric request signing;
- mTLS;
- OAuth client credentials;
- private network identity;
- cloud workload identity.

IdentityCore's current signing foundation uses versioned canonicalization, key identifiers, timestamps, nonces, request binding, and replay detection. See `docs/architecture/provider-signing.md`.

A provider response must be bound to the initiating invocation and should include:

- invocation ID;
- request ID;
- timestamp;
- provider key ID;
- signature version;
- response signature.

## 8. Idempotency

Every invocation must have an idempotency key or stable invocation ID.

A provider must not create duplicate side effects when IdentityCore retries a request after timeout or network failure.

For read-like capabilities such as OCR or face comparison, repeated execution should return the same semantic result for the same versioned inputs, subject to documented model nondeterminism.

For side-effecting capabilities such as credential issuance or notification delivery, idempotency is mandatory.

## 9. Normalized response

A provider response must separate transport success from capability outcome.

```json
{
  "contract_version": "1.0",
  "invocation_id": "pinv_...",
  "status": "completed",
  "outcome": "recognized",
  "confidence": 0.94,
  "evidence": [],
  "claims": [],
  "provider_metadata": {
    "provider_version": "1.4.0",
    "model_version": "ocr-model-7"
  },
  "warnings": []
}
```

Provider-specific fields should remain inside a namespaced metadata object unless promoted into a shared capability schema.

## 10. Error taxonomy

Providers should use stable machine-readable errors.

Required categories include:

- `invalid_request`;
- `unsupported_capability`;
- `unsupported_country`;
- `unsupported_document_type`;
- `evidence_unavailable`;
- `evidence_invalid`;
- `authentication_failed`;
- `rate_limited`;
- `timeout`;
- `temporarily_unavailable`;
- `malformed_response`;
- `processing_failed`;
- `inconclusive`.

Each error must declare whether retry is safe and whether changing provider may help.

## 11. Timeouts and retries

Providers must document expected latency and maximum processing time.

IdentityCore should enforce:

- connection timeout;
- read timeout;
- total invocation deadline;
- maximum response size;
- bounded retry count;
- retry only for approved error categories;
- exponential backoff with jitter;
- circuit-breaking or health-based suppression as the runtime matures.

A timeout does not mean the provider did not process the request. Idempotency is therefore required.

## 12. Asynchronous providers

Long-running providers may return an accepted state and complete through a signed callback.

An asynchronous contract must define:

- callback authentication;
- callback replay prevention;
- polling fallback;
- maximum completion window;
- cancellation behavior;
- duplicate callback handling;
- terminal state semantics.

The current platform is strongest around synchronous and task-mediated execution. General asynchronous provider contracts should be treated as evolving until fully implemented and tested.

## 13. Health and readiness

Providers should expose or support:

- readiness status;
- capability-level health;
- version information;
- dependency degradation;
- supported schema versions;
- optional latency and quota information.

IdentityCore must distinguish configuration failure, provider outage, capability outage, and regional unavailability.

## 14. Data protection declarations

Each provider registration should declare:

- data categories processed;
- processing purpose;
- storage behavior;
- retention duration;
- subprocessor usage;
- processing regions;
- cross-border behavior;
- encryption controls;
- deletion capabilities;
- incident notification expectations.

These declarations support policy and governance; they do not replace contractual or legal review.

## 15. Logging and redaction

Providers must never require IdentityCore to persist secrets or raw sensitive payloads in ordinary logs.

The runtime should redact:

- credentials and tokens;
- signed URLs;
- document numbers;
- biometric templates;
- raw media;
- provider secrets;
- internal network details where sensitive.

Diagnostic metadata should be structured, bounded, and safe for tenant-scoped audit and operations.

## 16. Conformance testing

A provider should pass a conformance suite before production activation.

The suite should test:

- capability manifest validity;
- request and response schema compatibility;
- signature verification;
- nonce and replay handling;
- idempotency;
- timeout behavior;
- malformed output handling;
- oversized response rejection;
- sensitive-field redaction;
- deterministic fixtures where applicable;
- tenant and environment isolation;
- deletion and retention declarations.

## 17. Deployment modes

### Managed in-process or internal service

Used by IdentityCore Managed Providers. These still pass through the provider adapter and invocation boundary.

### Remote HTTP

Used by commercial or customer-hosted providers reachable over approved network paths.

### Private network

Used for enterprise or government deployments with private connectivity.

### Embedded deployment

A future option for providers packaged into a dedicated deployment boundary. Embedded providers must still conform to capability and evidence contracts.

## 18. Versioning

Provider SDK compatibility has several independent versions:

- Provider SDK/manifest version;
- capability contract version;
- provider implementation version;
- adapter version;
- model version;
- evidence schema version.

IdentityCore should reject unsupported major versions and allow explicitly compatible minor versions.

## 19. Provider author checklist

Before production activation, a provider author should be able to answer:

1. Which capabilities and versions are implemented?
2. What evidence is required?
3. What evidence and claims are emitted?
4. How are requests authenticated and signed?
5. How is replay prevented?
6. Is execution idempotent?
7. Which errors are retryable?
8. Where is data processed and retained?
9. How is deletion handled?
10. Which conformance fixtures pass?
11. How is provider health reported?
12. Which operational limits apply?

## 20. Current implementation note

The repository already contains important Provider SDK foundations: adapter registration, centralized invocation, secure custom HTTP execution, message signing, replay prevention, redacted telemetry, versioned capability results, and provider-check persistence.

A complete published SDK package, machine-readable manifest, organization self-service onboarding flow, and full conformance harness remain work to complete before arbitrary providers should be advertised as plug-and-play production integrations.
