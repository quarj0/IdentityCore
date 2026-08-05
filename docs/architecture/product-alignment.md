# Product Alignment and Gap Assessment

Last reviewed: 2026-08-05

## Executive answer

IdentityCore is a **vendor-neutral identity infrastructure platform**. Identity verification is the first implemented workload, not the architectural boundary of the product.

The repository is now materially aligned with that direction. It contains working foundations for a Control Plane, workflow and policy versioning, a Provider Runtime, normalized provider results, evidence handling, Manual Review, privacy operations, audit integrity, APIs, SDKs, and hosted applications.

IdentityCore is not yet a complete identity operating system or provider marketplace. Advanced routing, broad provider conformance, reusable claims, tenant-owned storage, customer-managed keys, and production certification remain incomplete.

## Platform definition

IdentityCore owns the vendor-neutral infrastructure around identity operations:

- tenant, project, and environment isolation;
- APIs, SDKs, CLI, hosted journeys, and operator consoles;
- workflow, policy, and decision execution;
- provider registration, selection, invocation, and normalization;
- evidence lineage and claims foundations;
- Manual Review and maker-checker controls;
- consent, retention, export, deletion, and legal-hold handling;
- tamper-evident audit and signed result delivery.

Providers may be IdentityCore-managed, commercial, government-operated, customer-hosted, or infrastructure services such as storage, KMS/HSM, risk, and messaging.

## Current architecture

```text
Applications, SDKs, CLI and hosted journeys
                    |
                    v
           IdentityCore API Layer
                    |
       +------------+------------+
       |                         |
       v                         v
 Control Plane             Execution Plane

 tenants/projects          workflow engine
 environments              policy engine
 users/API clients         provider runtime
 workflows/policies        evidence
 provider configuration    decisions
 privacy rules             manual review
                            audit/webhooks
                    |
                    v
                 Providers
```

## Capability assessment

| Capability | Current maturity | Current reality and limitation |
| --- | --- | --- |
| Identity Control Plane | Implemented foundation | Tenants, organizations, projects, environments, users, roles, API clients, workflows, policies, providers, audit, privacy, and administration surfaces exist. Promotion, provider self-service, and unified operational controls remain incomplete. |
| Provider Runtime | Implemented foundation | Managed AI calls are routed through provider adapters and centralized invocation. Provider checks store normalized, versioned results, duration, status, errors, and redacted metadata. Advanced routing and fallback remain incomplete. |
| Secure custom HTTP providers | Implemented foundation | The repository includes secure HTTP provider invocation, endpoint controls, signing, timestamps, nonces, replay resistance, idempotency concepts, and versioned capability contracts. Broader conformance tooling and organization-facing onboarding remain planned. |
| Provider ecosystem | Early foundation | Provider records, assignments, adapters, and capability contracts exist. Discovery, certification, commercial metadata, residency declarations, pricing, and a provider marketplace remain future work. |
| Workflow Engine | Implemented foundation | Versioned workflows, workflow summaries, execution state, immutable snapshots, and hosted verification journeys exist. General cross-workload branching and provider-route composition remain partial. |
| Policy Engine | Implemented foundation | Verification policies, thresholds, required steps, retention settings, snapshots, and decision inputs exist. A generalized policy language and external policy-provider contract remain incomplete. |
| Decision Engine | Implemented foundation | Automatic decisions, reasoned outcomes, immutable input snapshots, Manual Review, and maker-checker approval exist. Broader workload-neutral decision contracts remain under development. |
| Evidence Model | Implemented foundation | Provider checks, document and biometric results, reports, model metadata, audit context, and decision snapshots provide a strong evidence foundation. A single generalized evidence resource and lineage API remain incomplete. |
| Claims Engine | Partial | OCR fields, normalized provider results, policy evaluation, and decision snapshots supply claim-like data. Reusable claims, conflict resolution, selective disclosure, expiry, revocation, and cross-workload reuse are not complete. |
| Identity verification workload | Working vertical slice | Consent, document selection and capture, OCR, quality, classification, selfie/liveness, face match, decisions, Manual Review, status, webhooks, and evidence access are represented. Production accuracy and country coverage remain deployment obligations. |
| IdentityCore Managed Providers | Working foundation | FastAPI hosts managed OCR, document quality, classification, face comparison, liveness/PAD, and model reporting. These are provider implementations, not privileged core components. |
| Manual Review | Implemented foundation | Reviewer scope, assignment, evidence access, decisions, escalation, maker-checker approval, state-transition controls, and audit records exist. Operational QA and workforce governance still require hardening. |
| Privacy and retention | Implemented foundation | Encrypted fields, media cleanup, retention periods, legal holds, subject export, subject deletion/pseudonymization, and audit events exist. Complete deletion propagation and deployment-specific compliance assurance still require validation. |
| Audit and compliance evidence | Implemented foundation | Audit events are append-only and hash-chained, with access controls and event recording across sensitive operations. External WORM storage, SIEM integration, and independent assurance remain future work. |
| Tenant and environment isolation | Implemented foundation | REST and GraphQL regression tests, API environment scoping, tenant-owned resources, and credential isolation exist. Production penetration testing and database-level defense in depth remain required. |
| Developer platform | Broad foundation | Public REST API, internal GraphQL, interactive OpenAPI explorer, Python/Java/.NET SDKs, Python CLI, examples, and developer portal are present. Contract completeness and release/version policy need continued work. |
| Provider-neutral storage and keys | Planned | S3-compatible storage exists at deployment level. Tenant-selected storage providers, storage-reference-only evidence, per-tenant KMS/HSM, and customer-managed key lifecycle are not implemented end to end. |
| Country and document coverage | Implemented foundation | Global and country-specific document definitions, West African candidates, Ghana support, MRZ checks, and configurable enablement exist. Broad certified coverage is not implied. |
| Production readiness | Partial | MFA, token rotation, security headers, retention workers, audit integrity, idempotency, upload quarantine, webhooks, monitoring foundations, and tests exist. Pilot readiness still requires deployment validation, model evaluation, incident exercises, backups, load tests, and independent security review. |

## Provider Runtime: what is real today

The following are implemented foundations:

- adapter-backed provider capability execution;
- IdentityCore Managed Providers using the adapter boundary;
- centralized invocation through provider checks;
- normalized and versioned provider results;
- request/response metadata redaction;
- duration and status tracking;
- provider failure normalization;
- secure custom HTTP invocation;
- message signing, timestamps, nonces, and replay detection;
- tenant provider assignments;
- provider-aware document and biometric tasks;
- Manual Review routing for unavailable or inconclusive evidence.

This corrects earlier documentation that said provider selection changed attribution while execution always bypassed a general runtime. That statement is no longer true.

## Material gaps

### 1. Advanced provider routing

The platform still needs mature, versioned routes that can select providers by:

- project and environment;
- workflow and step;
- country and document type;
- residency and data-transfer policy;
- cost and service tier;
- provider health and latency;
- ordered fallback chains;
- final Manual Review or fail-closed action.

### 2. Provider onboarding and conformance

The Provider SDK contract now has documentation, but the ecosystem still needs:

- machine-readable manifests;
- automated conformance suites;
- test fixtures and certification levels;
- organization-facing connection tests;
- credential rotation and promotion workflows;
- health, residency, retention, and commercial metadata.

### 3. Generalized evidence and claims APIs

Evidence exists across domain records, provider checks, reports, and decisions. The next stage is a unified evidence resource with explicit lineage and a claims lifecycle supporting provenance, conflict resolution, selective disclosure, expiry, revocation, and reuse.

### 4. Storage and key-provider neutrality

Object storage is configurable per deployment, but not yet generally routed per tenant, project, environment, or workflow. KMS/HSM and customer-managed keys require first-class capability contracts and lifecycle controls.

### 5. External registry and risk providers

Provider types and capability direction exist, but production-ready registry, authenticity, watchlist, and external risk-provider integrations need complete contracts, authorization models, and conformance testing.

### 6. Production assurance

Repository implementation does not by itself establish regulatory compliance or production accuracy. Required work includes:

- independent security testing;
- provider and model evaluation;
- representative liveness and biometric testing;
- backup and restore exercises;
- load and failure testing;
- incident-response exercises;
- deployment-specific residency and key-management validation;
- operational Manual Review quality controls.

## Documents and terminology

The following hierarchy should be used:

- [`ARCHITECTURE.md`](../../ARCHITECTURE.md) — canonical architectural vision.
- [`provider-runtime.md`](provider-runtime.md) — provider execution boundary.
- [`capability-model.md`](capability-model.md) — provider-neutral capability contracts.
- [`evidence-model.md`](evidence-model.md) — evidence provenance and lifecycle.
- [`claims-engine.md`](claims-engine.md) — claims direction and current maturity.
- [`platform-roadmap.md`](../foundation/platform-roadmap.md) — capability-based roadmap.
- [`managed-providers.md`](../providers/managed-providers.md) — IdentityCore-operated provider implementations.
- [`provider-sdk.md`](../providers/provider-sdk.md) — provider integration contract.

Use **Execution Plane**, not “AI data plane,” for the general runtime. Use **IdentityCore Managed Provider**, not “internal AI component,” when describing OCR, face match, liveness, classification, or document quality as executable capabilities.

## Accurate current positioning

> IdentityCore is building vendor-neutral identity infrastructure. Identity verification is its first working workload. The platform has implemented foundations for tenant and environment isolation, workflows, policies, provider execution, normalized evidence, decisions, Manual Review, privacy operations, audit integrity, APIs, SDKs, and managed providers. Advanced provider routing, broad conformance, reusable claims, tenant-owned storage, customer-managed keys, and production certification remain under development.

## Product claim boundaries

Do not claim that:

- every provider can already be connected without engineering work;
- every country or document is supported;
- managed OCR, face, or liveness models are certified for all production uses;
- IdentityCore provides a finished provider marketplace;
- reusable verified claims are complete;
- deployment configuration alone establishes legal compliance;
- any general accuracy percentage applies across providers, documents, countries, devices, and attack classes.

The platform should communicate direction boldly while describing implementation maturity precisely.
