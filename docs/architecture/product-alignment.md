# Product Alignment and Gap Assessment

Last reviewed: 2026-07-26

## Executive answer

IdentityCore's intended category is **identity infrastructure**, not merely identity
verification software and not a single end-to-end verification vendor. Its closest
conceptual analogy is a cloud platform for identification: it supplies a stable control
plane and common platform primitives, while organizations compose managed services,
specialist third-party providers, and customer-hosted systems.

Identity verification is the first workload and the current working vertical slice. It
proves the infrastructure through a policy-driven workflow, but it must not become the
architectural boundary of IdentityCore. The current repository is **directionally
aligned**, but it is **not yet the complete infrastructure platform described by that
vision**.

The ordinary verification path is substantially represented. The reusable control plane
and provider ecosystem are much earlier. Bring Your Own Provider (BYOP) is not an
enterprise add-on: it is a defining platform capability that allows OCR, biometric,
liveness, authenticity, registry, risk, storage, messaging, and other identity vendors
to plug into IdentityCore. BYOP is currently a foundation rather than a complete
orchestration system.

## Platform definition

IdentityCore should own the vendor-neutral infrastructure around identity operations,
not insist on performing every operation itself.

### Control plane

The control plane is where an organization configures and governs identity services:

- tenants, projects, environments, users, roles, and access policy;
- identity workflows, templates, policies, provider routes, and version promotion;
- provider onboarding, credentials, health, conformance, cost, and residency controls;
- consent purposes, evidence handling, retention, encryption, and audit policy;
- API clients, usage limits, observability, billing, and incident operations.

### Identity data plane

The data plane executes each identity operation through a consistent runtime:

- accept a request or start a session;
- collect only the consented evidence and claims required by policy;
- select providers using tenant, environment, workflow, country, document, residency,
  availability, performance, and cost rules;
- issue minimal, time-limited access to the selected provider;
- validate and normalize provider output into vendor-neutral evidence;
- retry or fall back without changing the organization's integration contract;
- apply policy, request human review where necessary, and return signed results;
- preserve lineage, auditability, retention, and deletion across the full operation.

### Provider ecosystem

A provider is a replaceable capability behind an IdentityCore contract. It may be:

- operated by IdentityCore;
- operated by the customer in its own network;
- supplied by an identity-verification company;
- a specialist OCR, biometrics, liveness, authenticity, fraud, or watchlist vendor;
- an authorized government, banking, educational, or professional registry;
- storage, KMS/HSM, messaging, or other supporting infrastructure.

This makes specialist and end-to-end identity companies potential ecosystem participants,
not merely competitors. A provider may expose one capability or several, and an
organization remains free to choose a different provider at every step.

### Platform services beyond the first verification workload

The shared primitives should support additional identification and digital-trust
services without creating separate silos. Examples include reusable verified claims,
selective age or eligibility assertions, registry-backed identity resolution,
credential issuance and validation, step-up or repeat authentication, deduplication,
account recovery, organizational identity, and program-specific eligibility workflows.
These are platform directions, not claims that all such services are implemented today.

IdentityCore should remain responsible for orchestration, governance, interoperability,
and evidence lineage. The organization remains responsible for the business consequence
of a result, while each provider remains responsible for the signal or infrastructure it
supplies.

## Capability assessment

| Product capability | Current maturity | Repository evidence and limitation |
| --- | --- | --- |
| Identity control plane | Early foundation | Tenants, projects, environments, access control, APIs, configuration surfaces, audit, and usage concepts exist, but they are not yet a unified provider-neutral control plane. |
| Provider marketplace/ecosystem | Early foundation | A provider registry and provider records exist. Provider discovery, capability manifests, conformance, commercial terms, residency metadata, certification, and organization self-service onboarding remain future work. |
| Vendor-neutral data plane | Partial | Normalized provider-check evidence exists, but built-in execution paths still bypass a general orchestration runtime. |
| Organization and tenant isolation | Implemented foundation | Organizations, tenants, projects, membership/access control, and tenant-scoped domain records exist. Production authorization and isolation still require security testing. |
| Templates, policies, and workflows | Implemented foundation | Templates, verification policies, versioned workflows, policy snapshots, and workflow UI exist. The runtime remains more fixed than the fully configurable orchestration vision. |
| Hosted applicant journey | Working vertical slice | Consent, country/document selection, upload/capture, selfie/liveness, mobile handoff, status, and completion views exist in the verification portal. |
| Document processing | Working vertical slice | Quality, classification, OCR, country definition modules, normalized evidence, and manual-review routing are implemented. Authenticity/forensics coverage is not yet a broad vendor-grade engine. |
| Biometrics | Working vertical slice | Selfie capture, active/passive liveness records, face comparison, thresholds, provider checks, and failure-to-review behavior exist. Production model validation and anti-spoof coverage remain deployment obligations. |
| Risk and decisions | Working vertical slice | The service aggregates evidence into risk recommendations and automatic decisions, with human review for uncertainty. The built-in engine is presently rule-oriented rather than a general external risk-engine contract. |
| Manual review | Implemented foundation | Reviewer assignment/access, evidence views, decisions, escalation, and audit records exist. Operational QA, maker-checker controls, and reviewer policy depth still need production hardening. |
| Signed result delivery | Implemented foundation | Webhook endpoints, HMAC signatures, attempts, exponential retries, and audit events exist. External contract/versioning and end-to-end integration certification remain. |
| Privacy, retention, and audit | Implemented foundation | Encrypted sensitive JSON, audit events, evidence reports, media retention cleanup, and access controls exist. A full compliance program, deletion/export workflows, residency guarantees, and formal assurance are not established merely by these models. |
| Dashboards and developer surfaces | Broad UI foundation | Organization dashboard, verification portal, platform administration, public website, and developer portal are present. Some administration screens are read-oriented, scaffolded, or backed by mock/sample data. |
| Country-aware support | Implemented foundation | Classification definitions include global documents, West African candidates, and Ghana. This is extensible, but it does not yet equal broad country/document production coverage. |
| Sandbox and production separation | Partial | Projects/environments, credentials, examples, and configuration concepts exist. A fully certified sandbox simulator and production promotion/control plane are not complete. |

## BYOP: what is real today

The repository already establishes several correct seams:

- Providers may be platform defaults or tenant-owned records.
- Provider configuration is stored in an encrypted JSON field.
- A tenant may assign one provider to OCR, classification, quality, face match,
  liveness, identity lookup, risk, or a notification channel.
- Provider checks retain the selected provider, status, timestamps, error information,
  request/response metadata, and a normalized result.
- Internal document and biometric calls are represented through provider-check records.
- Notification delivery supports tenant selection and adapter-based extension.
- Unknown or unavailable AI results are generally routed toward manual review rather
  than silently approved or discarded.

These are useful architectural foundations, but they do not by themselves make the
platform a general BYOP orchestrator or identity-infrastructure control plane.

## BYOP: material gaps

1. **Execution does not follow the selected provider for core AI checks.** Provider
   resolution selects and records a tenant assignment, but document, liveness, and face
   tasks still call the built-in AI-service client. A tenant OCR assignment therefore
   changes attribution, not the executable adapter.
2. **There is no generic custom HTTP provider contract.** Endpoint validation,
   authentication modes, signed requests/responses, replay protection, response mapping,
   schema/version negotiation, and per-capability adapters are not implemented as a
   reusable runtime.
3. **Assignments are one-per-tenant/per-capability.** There are no ordered provider
   chains, conditional country/document routing rules, template-level overrides, retry
   policies, circuit breakers, or a final manual fallback configuration.
4. **Provider administration is incomplete.** The platform console can inspect provider
   data, but organization administrators do not yet have the complete add, map, test,
   sandbox, promote, rotate, and health-check workflow described in the vision.
5. **Storage is deployment-wide, not tenant-routed.** S3-compatible storage is supported,
   including separate bucket purposes and signed URLs, but there is no tenant-owned
   object-storage provider assignment or storage-reference-only evidence model.
6. **Customer-managed encryption keys are not implemented.** Application encryption is
   valuable, but it is not BYOK/KMS/HSM integration with per-tenant and per-environment
   key lifecycle controls.
7. **Registry and external risk execution are not complete.** Types and assignment keys
   exist, but an authoritative-registry connector framework and an external risk-engine
   invocation/normalization path are not present end to end.
8. **Authenticity is not a first-class provider capability.** Document checks currently
   cover useful quality/classification/OCR signals, but the provider taxonomy lacks a
   dedicated authenticity check and country-specific authenticity routing.
9. **Operational controls need hardening.** Provider health metrics, redacted telemetry,
   egress allowlists, secret rotation, data-processing declarations, residency controls,
   and auditable fallback reasons need complete enforcement.

## Recommended implementation order

### 1. Make provider selection executable

Introduce a capability adapter interface and registry. Every processing task should ask
an orchestrator to execute a capability; the orchestrator should resolve the provider,
invoke its adapter, validate and normalize the result, and update the provider attempt.
The built-in AI service should become one adapter, not a special hard-coded path.

The same orchestration API must be used for IdentityCore-managed, customer-hosted, and
third-party providers. Otherwise BYOP will remain a label attached to built-in execution
instead of a true platform boundary.

### 2. Model routes, chains, and attempts

Add versioned, environment-scoped provider routes with conditions for country, document
type, template/workflow, and capability. A route should contain ordered providers plus
timeouts, retry policy, and a final action. Record each invocation separately so a check
can show `internal OCR timed out -> default OCR succeeded -> normalized result`.

### 3. Ship a secure custom HTTP adapter

Define versioned request/response schemas, minimal evidence grants, short-lived signed
URLs, HMAC or asymmetric signatures, timestamps/nonces, idempotency keys, strict timeout
limits, response-size limits, confidence validation, and log redaction. Protect outbound
requests against SSRF with approved destinations and network egress policy.

### 4. Add organization-facing configuration and promotion

Build **Settings -> Providers** for create, credential setup, mapping, connection tests,
sample cases, health, assignment, fallback configuration, and sandbox-to-production
promotion. Production activation should require appropriate roles and fresh validation.

### 5. Define the provider platform contract

Publish capability manifests and conformance requirements so both specialist providers
and broader identity vendors can integrate without IdentityCore-specific code being
added to every workflow. A manifest should describe supported capabilities, countries,
documents, input/evidence requirements, output schema versions, deployment modes,
residency, retention, health, pricing/metering dimensions, and certification status.

### 6. Extend capability coverage

Add first-class authenticity, registry, external risk, object storage, and key-management
adapters. Storage and key management should be designed deliberately because they affect
the location, accessibility, retention, and deletion of the platform's most sensitive
evidence.

### 7. Prove production behavior

Add contract suites for adapters; end-to-end tests for timeout, malformed response,
fallback, replay, tenant isolation, and manual-review outcomes; provider conformance
fixtures; load/failure testing; security review; and documented operational runbooks.

## Product wording until then

Accurate current wording is:

> IdentityCore is building vendor-neutral identity infrastructure. Identity verification
> is its first working workload. The platform already has tenant, workflow, evidence,
> policy, audit, and provider foundations, while the general provider execution plane,
> conditional routing, fallback chains, provider ecosystem, tenant-owned storage, and
> customer-managed keys remain under development.

Avoid claiming that arbitrary OCR, liveness, face, registry, risk, storage, or key
providers can already be connected safely in production until their execution paths and
operational controls have been implemented and tested.
