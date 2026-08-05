# Capability Model

## Purpose

A capability is a stable, versioned operation that IdentityCore can request from a
provider. Capabilities separate **what a workflow needs** from **who performs it**.

A workflow requests `document.ocr`; it does not request PaddleOCR, a commercial IDV
vendor, or a government endpoint directly.

## Design goals

The capability model must:

- keep workflows and policies vendor-neutral;
- support managed, commercial, government, and customer-hosted implementations;
- define normalized inputs, outputs, failures, and evidence;
- allow contract evolution without silently changing historical meaning;
- support country, document, residency, and environment constraints;
- enable provider conformance testing;
- preserve evidence provenance and decision reproducibility.

## Capability identifier

Capabilities use stable, namespaced identifiers:

```text
<domain>.<operation>
```

Examples:

```text
document.quality
document.classification
document.ocr
document.authenticity
biometric.face-detection
biometric.face-match
biometric.liveness
identity.registry-lookup
risk.assessment
storage.object
key-management
notification.delivery
```

Identifiers describe business-neutral technical operations. Provider names, model names,
and country brands do not belong in capability IDs.

## Contract version

Every capability invocation references a contract version. The version defines:

- input schema;
- output schema;
- allowed evidence types;
- normalized statuses and reason codes;
- error and retry semantics;
- required provenance and observability fields;
- compatibility guarantees.

A provider may support multiple versions during migration. A running workflow retains the
resolved contract version as part of its execution and evidence history.

## Capability contract

A capability contract should declare:

### Identity

- capability ID;
- contract version;
- lifecycle status: experimental, preview, stable, deprecated;
- owning platform domain.

### Input

- required and optional fields;
- accepted evidence types and schema versions;
- maximum file or payload sizes;
- synchronous or asynchronous behavior;
- purpose and consent requirements;
- idempotency requirements.

### Output

- normalized result schema;
- evidence types emitted;
- score ranges and confidence representation;
- model/provider version fields;
- reason and issue codes;
- provenance requirements.

### Failure

- timeout behavior;
- retryability;
- unsupported-input semantics;
- malformed-response behavior;
- unavailable and authentication states;
- final safe workflow action when no provider succeeds.

### Constraints

- supported countries or jurisdictions;
- supported document families;
- deployment modes;
- residency and processing-location declarations;
- retention and deletion obligations;
- required certification or assurance.

## Capability families

### Document capabilities

#### `document.quality`

Determines whether a capture is usable. It may emit blur, glare, crop, resolution,
orientation, obstruction, and lighting evidence.

It does not determine that a document is genuine.

#### `document.classification`

Identifies or narrows the likely document type and country using visible, OCR, structural,
MRZ, barcode, or other evidence.

Unknown, unsupported, ambiguous, and insufficient-evidence states are valid normalized
outcomes and must not be silently converted into rejection or approval.

#### `document.ocr`

Extracts text and structured candidate fields. OCR output is unverified evidence until
normalized, corroborated, and evaluated by policy.

#### `document.authenticity`

Produces signals related to structural consistency, security features, issuer validation,
tampering, replay, or other authenticity risks. This is a distinct capability from OCR
and quality and should not be implied by them.

### Biometric capabilities

#### `biometric.face-detection`

Locates faces and emits detection, count, quality, landmarks, and model metadata.

#### `biometric.face-match`

Compares two permitted face representations and emits a similarity result, threshold
context, quality, and model metadata. It does not issue a business decision.

#### `biometric.liveness`

Evaluates active or passive liveness and presentation-attack evidence. Contracts must
identify the method, challenge where applicable, model version, result, confidence, and
failure reason.

### Identity capabilities

#### `identity.registry-lookup`

Queries an authorized source for identity, document, credential, membership, or
eligibility evidence. The contract must define legal authorization, query minimization,
matching semantics, and authoritative-source provenance.

### Risk capabilities

#### `risk.assessment`

Evaluates declared signals and emits explainable risk evidence and reason codes. Risk
providers may inform policy but do not own the final organizational decision.

### Infrastructure capabilities

#### `storage.object`

Stores or retrieves evidence objects under retention, residency, encryption, and access
requirements. Tenant-routed storage remains an architectural direction until fully
implemented.

#### `key-management`

Performs key wrapping, signing, encryption, or key lifecycle operations through managed
KMS or HSM systems. Customer-managed key routing remains planned where not implemented.

#### `notification.delivery`

Delivers an email, SMS, or other notification using a normalized delivery contract and
records attempts and provider outcomes.

## Provider capability declaration

A provider capability declaration should include:

- capability ID and supported contract versions;
- provider and adapter versions;
- countries, document types, languages, and input formats;
- synchronous/asynchronous mode;
- endpoint or deployment mode;
- limits, timeouts, and expected latency;
- residency and retention declarations;
- health/readiness information;
- pricing or metering dimensions where applicable;
- conformance and certification status.

A provider implementing many operations remains a collection of capabilities. Workflows
must not be forced to consume the provider's entire end-to-end product.

## Capability selection

Selection may consider:

- tenant and environment assignment;
- workflow and policy version;
- country and document type;
- data residency;
- provider availability and health;
- evidence type and size;
- certification requirements;
- cost and latency policy;
- customer preference;
- previous attempt outcomes.

The current implementation supports provider records, assignments, adapter resolution,
and capability invocation foundations. Documentation should distinguish these from the
full target of conditional routing and ordered fallback chains.

## Normalized status

All capabilities share common invocation states where possible:

```text
pending
processing
succeeded
failed
timeout
unavailable
unsupported
cancelled
```

Capability-specific output adds domain result states such as `recognized`, `ambiguous`,
`matched`, `not_matched`, `live`, `spoof_suspected`, or `inconclusive`.

Invocation state and domain result must not be conflated. For example, an invocation can
succeed while correctly returning `unsupported` input evidence or an inconclusive domain
result.

## Evidence emission

A successful capability invocation emits one or more evidence records containing:

- capability and contract version;
- provider and adapter identity;
- provider/model version;
- normalized result;
- status, confidence, quality, and reason codes;
- parent evidence references;
- processing timestamps and duration;
- integrity, retention, and redaction metadata.

Provider payloads should not become a permanent vendor-specific extension of core domain
models. Raw provider responses may be retained only where justified, protected, and
versioned; normalized evidence is the platform contract.

## Compatibility

A new contract version is required when a change can alter interpretation, validation, or
decision behavior. Additive optional fields may remain compatible when consumers are
required to ignore unknown fields.

Providers and SDKs should support an overlap period during version migration. Historical
workflow and decision snapshots continue to reference the original version.

## Conformance

Each stable capability should have reusable fixtures and contract tests covering:

- valid minimum and full requests;
- valid normalized responses;
- unsupported and inconclusive outcomes;
- malformed fields, score bounds, and oversized payloads;
- timeout and retry behavior;
- idempotency;
- signing and replay resistance for remote providers;
- evidence provenance;
- redaction;
- version compatibility.

## Governance

Adding or materially changing a capability requires:

1. A documented problem and workload use case.
2. A provider-neutral contract.
3. Security and privacy review.
4. Evidence and claim mapping.
5. Failure and Manual Review behavior.
6. Contract fixtures and tests.
7. API/SDK/documentation updates.
8. An ADR when the change establishes a significant platform boundary.

## Related documentation

- [Canonical Architecture](../../ARCHITECTURE.md)
- [Provider Runtime](provider-runtime.md)
- [Evidence Model](evidence-model.md)
- [Claims Engine](claims-engine.md)
