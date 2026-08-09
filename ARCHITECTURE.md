# IdentityCore Architecture

> **Canonical architecture document**
>
> IdentityCore is a vendor-neutral identity infrastructure platform. Identity verification is the first workload built on the platform; it is not the platform boundary.

## 1. Why identity infrastructure

Most identity systems are assembled from disconnected products: document verification, biometrics, registries, risk engines, storage, key management, human review, and audit tooling. Each integration introduces a different contract, evidence format, operational model, and compliance boundary.

IdentityCore provides the common infrastructure around those capabilities. Applications integrate once with IdentityCore, while organizations choose which managed, commercial, government, or customer-hosted providers execute each capability.

IdentityCore therefore competes primarily with fragmentation and vendor lock-in—not by requiring every customer to use one verification vendor.

## 2. Identity Operating System

The "Identity Operating System" describes IdentityCore's role as the layer that coordinates identity workloads in the same way an operating system coordinates applications and hardware.

IdentityCore supplies reusable platform primitives:

- tenant, project, and environment isolation;
- APIs, SDKs, CLI, webhooks, and hosted journeys;
- workflow, policy, and decision execution;
- provider discovery, selection, invocation, and normalization;
- evidence lineage and claims;
- manual review and maker-checker controls;
- consent, privacy, retention, deletion, and export controls;
- tamper-evident audit and operational observability.

A workload composes those primitives for a business purpose. Identity verification is workload one. Future workloads may include registry-backed identity resolution, reusable verified claims, age or eligibility assertions, credential issuance and validation, account recovery, step-up identity checks, organizational identity, and program-specific trust workflows.

## 3. Architectural principles

1. **Provider neutrality.** Core domains depend on capability contracts, not vendor APIs.
2. **Workloads are compositions.** Verification is assembled from reusable platform primitives.
3. **Evidence before decisions.** Providers produce technical evidence; policies and authorized humans determine outcomes.
4. **No privileged managed path.** IdentityCore Managed Providers use the same runtime boundary as external providers.
5. **Version everything that affects trust.** Workflows, policies, provider contracts, evidence schemas, models, and decision inputs are versioned.
6. **Tenant and environment isolation.** Every control-plane and execution-plane operation is scoped.
7. **Privacy by construction.** Evidence access is minimal, time-limited, auditable, retained only as required, and deletable.
8. **Failure is explicit.** Timeout, unavailable, malformed, unsupported, inconclusive, and policy failure are distinct states.
9. **Human review is a first-class execution path.** It is not an exception hidden outside the workflow.
10. **Current implementation and target architecture must be labeled honestly.** Documentation must not claim planned capabilities are production-ready.

## 4. Platform architecture

```text
Applications, SDKs, CLI, hosted journeys and operator consoles
                              |
                              v
                     IdentityCore API Layer
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
       Control Plane                    Execution Plane

  Tenants and organizations        Workflow Engine
  Projects and environments        Policy Engine
  Users, roles and API clients     Provider Runtime
  Workflow definitions             Evidence and lineage
  Policy versions                  Claims processing
  Provider registrations           Decision Engine
  Provider assignments/routes      Manual Review
  Privacy and retention rules      Audit and event delivery
  Operational configuration
             |                                 |
             +----------------+----------------+
                              |
                              v
                           Providers

  IdentityCore Managed Providers | Commercial IDV vendors
  Government/authoritative registries | Customer-hosted services
  Risk providers | Storage providers | KMS/HSM providers
  Messaging and other supporting infrastructure
```

## 5. Control Plane

The Control Plane configures and governs identity operations. It does not directly perform OCR, liveness, registry lookup, or other provider capabilities.

Its responsibilities include:

- organizations, tenants, projects, and sandbox/production environments;
- users, roles, API clients, scopes, and privileged-action controls;
- versioned workflows, templates, policies, and promotion;
- provider registration, credentials, capability declarations, assignments, and health;
- country, document, residency, retention, and privacy configuration;
- audit policy, webhook configuration, usage controls, and operational settings.

The current repository contains substantial foundations for tenants, projects, environments, workflows, policies, provider records, API clients, audit, privacy operations, dashboards, and platform administration. Some control-plane experiences remain incomplete or operator-oriented.

## 6. Execution Plane

The Execution Plane runs an identity operation from request to auditable outcome.

A typical execution is:

1. Authenticate and resolve tenant, project, environment, and subject context.
2. Load immutable workflow and policy snapshots.
3. Determine the evidence or claims required for the requested workload.
4. Resolve a provider for each capability.
5. Grant only the evidence access needed for that invocation.
6. Invoke the provider through the Provider Runtime.
7. Validate, normalize, version, and persist the result as evidence.
8. Evaluate policy and risk rules.
9. Continue, retry, fall back, request more evidence, or enter Manual Review.
10. Persist the decision inputs and resulting decision.
11. Emit audit events, notifications, and signed webhooks.
12. Apply retention, export, and deletion controls throughout the lifecycle.

## 7. Provider Runtime

The Provider Runtime is the execution boundary between IdentityCore and capability providers.

It is responsible for:

- resolving the selected provider and adapter;
- validating capability compatibility;
- constructing minimal provider requests;
- applying authentication, signing, timestamps, nonces, and idempotency;
- enforcing endpoint, timeout, response-size, and egress controls;
- recording each provider check or attempt;
- normalizing vendor-specific output into versioned IdentityCore evidence;
- redacting sensitive telemetry;
- exposing deterministic failure semantics to workflows;
- supporting retry, fallback, and Manual Review policies.

The repository now includes adapter-backed managed AI execution, centralized provider invocation, secure HTTP provider calls, provider message signing and replay resistance, redacted telemetry, duration tracking, versioned capability results, immutable environment-scoped provider routes, and tenant/environment-scoped health views. Routes can match capability, country, document type, and workflow; enforce per-attempt timeouts and bounded retries; execute ordered fallback; recover open circuits through a single half-open probe; and finish with Manual Review or a failed verification. Operators can inspect availability, error rate, latency, and route circuit state without access to provider secrets or payloads. Conformance tooling and organization self-service provider onboarding remain areas of continued development.

See [Provider Runtime](docs/architecture/provider-runtime.md).

## 8. Capability model

A capability is a stable operation contract independent of the provider that implements it.

Examples include:

- `document.quality`
- `document.classification`
- `document.ocr`
- `document.authenticity`
- `biometric.face-match`
- `biometric.liveness`
- `identity.registry-lookup`
- `risk.assessment`
- `storage.object`
- `key-management`
- `notification.delivery`

A capability contract defines versioned inputs, allowed evidence access, normalized outputs, error semantics, observability requirements, and conformance expectations. A provider may implement one or many capabilities.

## 9. Workflows

A workflow defines the ordered and conditional execution of identity capabilities and human actions. It describes **what must happen**, not which vendor must perform it.

Workflow versions must be immutable once used. A running operation retains a snapshot so later configuration changes cannot silently alter its historical meaning.

Identity verification currently composes consent, document capture, quality, classification, OCR, selfie/liveness, face comparison, policy evaluation, Manual Review, audit, and result delivery.

## 10. Policies and decisions

The Policy Engine evaluates evidence, claims, context, and workflow state. Policies may determine:

- required evidence;
- acceptable document or country combinations;
- thresholds and confidence boundaries;
- retries and fallback behavior;
- automatic outcomes allowed for a workload;
- Manual Review and maker-checker requirements;
- retention and disclosure rules.

The Decision Engine records the outcome produced from versioned inputs. Provider output is never itself the final organizational decision. IdentityCore records the policy version, evidence references, reasons, reviewer actions, and any approval chain used to reach an outcome.

## 11. Evidence model

Evidence is an immutable or append-only record of what was observed, supplied, or produced during an identity operation.

Evidence must retain:

- type and schema version;
- source provider and capability;
- provider/model/adapter version where applicable;
- subject, tenant, project, environment, workflow, and operation context;
- timestamps and processing duration;
- confidence, quality, and status;
- provenance and parent evidence references;
- integrity metadata;
- retention classification and deletion state;
- redacted diagnostic metadata.

Raw media, normalized fields, biometric scores, registry responses, device signals, reviewer findings, and provider failures may all be evidence. Evidence does not automatically become a trusted claim or final decision.

See [Evidence Model](docs/architecture/evidence-model.md).

## 12. Claims

A claim is a normalized statement about a subject or organization, such as a name, date of birth, document expiry, age-over threshold, registry membership, or policy-satisfied identity attribute.

Claims must remain linked to supporting evidence and policy. IdentityCore distinguishes:

- extracted claims;
- provider-asserted claims;
- normalized claims;
- corroborated or policy-satisfied claims;
- derived claims.

A generalized Claims Engine is a platform direction with foundations in extracted fields, normalized results, evidence snapshots, and decisions. Documentation must not imply that reusable cross-workload claims are complete until lifecycle, conflict resolution, selective disclosure, and revocation are implemented.

See [Claims Engine](docs/architecture/claims-engine.md).

## 13. Manual Review

Manual Review is a governed execution capability for uncertain, unsupported, exceptional, or high-impact cases.

It includes:

- tenant-scoped assignment and reviewer authorization;
- evidence access appropriate to the case;
- reason codes, notes, and escalation;
- maker-checker approval where required;
- immutable decision history and audit events;
- protection against state-transition races and repeated actions.

Human review does not bypass policy, privacy, or audit controls.

## 14. Multi-tenancy and environments

Tenant isolation is mandatory across REST, GraphQL, background jobs, evidence, providers, Manual Review, webhooks, and audit.

Projects and environments separate sandbox and production credentials, workflows, policies, providers, and results. An API credential may only operate within its environment. Cross-tenant and cross-environment access should fail without disclosing whether a foreign resource exists.

## 15. Provider ecosystem

A provider is any replaceable implementation behind an IdentityCore capability contract.

### IdentityCore Managed Providers

IdentityCore-operated implementations currently include selected OCR, document quality, document classification, face comparison, liveness/PAD, and related processing hosted by the internal AI service. They are convenient defaults, not privileged architectural components.

### Commercial providers

Specialist or end-to-end IDV vendors may implement document, biometric, authenticity, fraud, watchlist, or registry capabilities.

### Government and authoritative providers

Authorized registries may provide identity lookup, credential validation, eligibility, or issuer-backed evidence.

### Customer-hosted providers

Organizations may run capabilities in their own network or deployment boundary.

### Infrastructure providers

Storage, KMS/HSM, messaging, and risk infrastructure can participate through capability contracts as the platform evolves.

## 16. Privacy, audit, and compliance

IdentityCore treats privacy operations as platform execution, not policy text alone.

The repository includes foundations for encrypted sensitive data, retention cleanup, subject export, subject deletion, evidence access control, tamper-evident audit events, signed webhook delivery, MFA for privileged accounts, and API credential rotation.

Production assurance additionally requires deployment-specific key management, backups, monitoring, incident response, legal configuration, model evaluation, provider agreements, residency controls, and independent security testing.

## 17. Current implementation shape

IdentityCore currently uses:

- a modular Django backend for core domains and public/internal APIs;
- Celery and Redis for asynchronous execution;
- PostgreSQL for relational state;
- S3-compatible object storage for media and evidence objects;
- a FastAPI service hosting IdentityCore Managed AI Providers;
- Next.js applications for marketing, organization, developer, verification, and platform-administration experiences;
- Python, JavaScript/TypeScript, Java, and .NET SDKs plus a Python CLI.

Identity document and biometric workers use durable database-backed jobs with
leases, heartbeats, bounded recovery attempts, and terminal Manual Review
routing. See [Processing job recovery](docs/operations/processing-job-recovery.md).

Public consumers retrieve decisions through a dedicated versioned verification
result contract. It exposes immutable policy/workflow versions and allowlisted
check provenance without applicant fields, storage references, raw provider
payloads, reviewer notes, or database primary keys.

This modular-monolith architecture is intentional. Components should be extracted only where scaling, security, deployment ownership, or availability boundaries justify it.

## 18. Future workloads

The platform primitives are intended to support additional workloads without creating separate identity silos. Candidate workloads include:

- reusable verified claims;
- selective age and eligibility assertions;
- registry-backed identity resolution;
- digital credential issuance and validation;
- step-up identity checks and repeat authentication;
- deduplication and account recovery;
- employee, student, vendor, and organizational identity;
- government and program-specific trust workflows.

These are architectural directions, not claims of current production completeness.

## 19. Architectural boundaries

IdentityCore must not:

- hardcode one country or provider into core domain contracts;
- make managed AI services the only execution path;
- treat model scores as final high-impact decisions;
- expose raw biometric templates through public APIs;
- retain sensitive evidence indefinitely;
- allow provider integrations to bypass tenant, environment, privacy, or audit controls;
- claim provider, country, model, or workload support that has not been implemented and tested.

## 20. Documentation authority

- This file defines the canonical architectural vision.
- ADRs record accepted decisions and supersession history.
- Detailed files under `docs/architecture/` define platform primitives.
- Workload documentation describes compositions built on those primitives.
- Provider documentation describes implementations and integration contracts.
- API/OpenAPI documentation remains the source of truth for concrete public endpoints.
- Implementation documents must label differences between current maturity and target architecture.
