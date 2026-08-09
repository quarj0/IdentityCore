# IdentityCore Platform Roadmap

Last reviewed: 2026-08-09

> IdentityCore is vendor-neutral identity infrastructure. Identity verification is the first workload built on the platform.

This roadmap is organized by platform capability rather than by the order in which repository folders were created.

Maturity labels describe repository capabilities, not deployment certification. The
[implementation backlog](../planning/implementation-backlog.md) defines acceptance
boundaries, while live GitHub issues and merged pull requests determine current work and
completion state.

## Maturity labels

- **Implemented** — present with meaningful automated coverage and an established execution path.
- **Implemented foundation** — substantial working support exists, but production hardening or broader coverage remains.
- **Partial** — some components exist, but the capability is not complete end to end.
- **Planned** — accepted platform direction without a complete implementation.
- **Exploratory** — research direction, not a product commitment.

## 1. Platform kernel

### Tenant and organization model — Implemented foundation

Current foundations:

- organizations and tenants;
- tenant-scoped domain records;
- organization memberships and roles;
- REST and GraphQL isolation regression coverage;
- platform administration surfaces.

Next outcomes:

- deeper authorization assurance;
- enterprise organizational hierarchy where required;
- clearer delegated-administration controls;
- production isolation testing and operational runbooks.

### Projects and environments — Implemented foundation

Current foundations:

- project and environment concepts;
- API credentials scoped to sandbox or production;
- environment isolation for API workflows;
- environment-aware webhooks and resources.

Next outcomes:

- controlled promotion between environments;
- environment-specific provider routes;
- approval requirements for production activation;
- environment configuration comparison and drift reporting.

### API, SDK and CLI surfaces — Implemented foundation

Current foundations:

- public REST API;
- internal GraphQL API;
- interactive OpenAPI explorer;
- Python, JavaScript/TypeScript, Java and .NET SDKs;
- production-oriented Python CLI;
- API clients, scopes and secret rotation.

Next outcomes:

- stable versioning policy;
- broader contract tests across SDKs;
- generated examples for all supported workflows;
- provider SDK packaging and conformance tooling.

## 2. Workflow, policy and decision platform

### Workflow Engine — Implemented foundation

Current foundations:

- workflow definitions and versions;
- workflow summaries in SDKs;
- immutable workflow snapshots for running verifications;
- hosted verification journey;
- background task coordination.

Next outcomes:

- a more general node and transition model;
- capability-driven workflow steps;
- conditional branching based on evidence and claims;
- explicit retries, fallbacks and compensation;
- reusable workflow templates beyond verification.

### Policy Engine — Implemented foundation

Current foundations:

- verification policies;
- versioned policy snapshots;
- configurable thresholds and requirements;
- retention-related policy data;
- policy-driven automatic and manual outcomes.

Next outcomes:

- provider-neutral policy expressions;
- policy simulation and explainability;
- jurisdiction and residency constraints;
- promotion and approval controls;
- policy reuse across future workloads.

### Decision Engine — Implemented foundation

Current foundations:

- persisted decision records;
- versioned decision input snapshots;
- reason codes and evidence summaries;
- automatic and manual decisions;
- maker-checker approval support;
- atomic state transitions.

Next outcomes:

- generalized decision contracts beyond verification;
- signed decision attestations;
- richer explanation graphs;
- decision revocation and supersession;
- configurable external decision/risk providers.

## 3. Provider platform

### Provider registry and assignments — Implemented foundation

Current foundations:

- provider records;
- tenant-owned and platform-managed providers;
- encrypted provider configuration;
- capability assignment concepts;
- platform administration views.

Next outcomes:

- machine-readable manifests;
- organization self-service onboarding;
- capability/country/document discovery;
- residency, commercial and certification metadata;
- provider lifecycle and deprecation controls.

### Provider Runtime — Implemented foundation

Current foundations:

- provider adapter protocol and registry;
- built-in AI capabilities routed through adapters;
- centralized invocation and ProviderCheck lifecycle;
- normalized and versioned results;
- secure custom HTTP provider calls;
- message signing and replay resistance;
- duration tracking and redacted telemetry.

Next outcomes:

- ordered fallback chains;
- richer conditional routing;
- circuit breakers and health-aware selection;
- asynchronous provider callback contracts;
- evidence-grant service;
- complete conformance suite;
- provider route simulation and promotion.

### Provider SDK — Partial

Current foundations:

- adapter and invocation contracts in code;
- deterministic signing fixture;
- secure HTTP adapter behavior;
- capability result versioning.

Next outcomes:

- published Provider SDK specification;
- machine-readable provider manifest;
- reference implementations;
- local provider test harness;
- conformance certification workflow;
- provider developer portal experience.

### IdentityCore Managed Providers — Implemented foundation

Current foundations:

- document quality;
- document classification;
- OCR;
- face comparison;
- liveness and PAD-related processing;
- mock, hybrid and real runtime modes;
- model metadata and Manual Review fallback.

Next outcomes:

- stronger model evaluation and calibration;
- expanded country/document support;
- authenticity signals;
- operational monitoring and drift analysis;
- capability-level deployment and scaling;
- published limitations and evaluation reports.

## 4. Evidence and claims

### Evidence Model — Implemented foundation

Current foundations:

- document and biometric records;
- provider checks and normalized results;
- evidence reports;
- workflow and decision snapshots;
- model/provider version metadata;
- retention cleanup and legal holds;
- tamper-evident audit facts.

Next outcomes:

- canonical cross-capability evidence envelope;
- explicit evidence lineage graph;
- storage-reference abstraction;
- integrity attestations for evidence objects;
- evidence access grants;
- provider-neutral evidence query APIs.

### Claims Engine — Partial

Current foundations:

- OCR extracted fields;
- normalized provider results;
- policy evaluation;
- evidence-backed decisions;
- redacted subject export.

Next outcomes:

- canonical claim schema;
- provenance and confidence per claim;
- conflict resolution;
- corroboration rules;
- reusable claims across workloads;
- selective disclosure;
- expiry, revocation and supersession;
- claim issuance and consumption APIs.

## 5. Privacy, audit and compliance

### Consent and purpose — Implemented foundation

Current foundations:

- consent records and versions;
- verification purpose;
- subject-facing consent flow;
- audit events.

Next outcomes:

- purpose-bound evidence grants;
- consent withdrawal handling;
- reusable consent receipts;
- policy enforcement across providers and workloads.

### Retention and deletion — Implemented foundation

Current foundations:

- retention cleanup workers;
- object deletion controls;
- legal holds;
- subject deletion and pseudonymization;
- redacted, expiring subject exports;
- deletion and export audit events.

Next outcomes:

- deletion propagation to all external providers;
- tenant-configurable retention classes;
- verification of object deletion;
- KMS-backed crypto-erasure where applicable;
- privacy request operator workflows and reporting.

### Audit — Implemented foundation

Current foundations:

- append-only audit events;
- per-tenant hash chaining;
- audit verification service;
- authentication, provider, review, privacy and verification events.

Next outcomes:

- concurrency-safe chain construction at scale;
- export to WORM/SIEM systems;
- signed audit checkpoints;
- richer actor and delegation context;
- compliance reporting and anomaly detection.

### Key and storage control — Partial

Current foundations:

- encrypted sensitive fields;
- S3-compatible object storage;
- purpose-specific buckets and signed URLs;
- secret validation and rotation foundations.

Next outcomes:

- tenant-routed storage providers;
- BYOK with KMS/HSM providers;
- per-environment key lifecycle;
- evidence-reference-only execution;
- residency and deletion assurance.

## 6. Manual Review and operations

### Manual Review — Implemented foundation

Current foundations:

- reviewer assignment and scope enforcement;
- evidence inspection;
- approve, reject and further-review actions;
- decision history;
- maker-checker approval;
- audit records and atomic transitions.

Next outcomes:

- configurable review queues and service levels;
- quality assurance sampling;
- reviewer calibration;
- escalations and specialist routing;
- workload-neutral review tasks;
- advanced redaction and least-privilege evidence views.

### Observability and incident operations — Partial

Current foundations:

- structured application and task logs;
- provider duration and status;
- health/readiness endpoints;
- webhook attempts;
- audit events;
- container monitoring foundations.

Next outcomes:

- end-to-end tracing;
- capability and provider SLOs;
- route health dashboards;
- incident workflows;
- privacy-safe metrics;
- production runbooks and failure exercises.

## 7. Identity verification workload

### Hosted subject journey — Implemented foundation

Current foundations:

- secure session links;
- consent;
- country and document selection;
- upload/capture;
- mobile handoff;
- selfie and liveness journey;
- progress and completion states.

Next outcomes:

- accessibility hardening;
- broader browser/device validation;
- stronger replay/media-injection controls;
- configurable workload steps;
- localization and regional customization.

### Document evidence — Implemented foundation

Current foundations:

- capture and upload lifecycle;
- quality analysis;
- document classification;
- OCR;
- MRZ-related logic;
- country/document definitions;
- unknown/unsupported routing to Manual Review.

Next outcomes:

- document authenticity as a first-class capability;
- broader issuer-backed validation;
- barcode/NFC/signature integrations;
- expanded document coverage;
- calibrated fraud signals and reviewer localization.

### Biometrics and liveness — Implemented foundation

Current foundations:

- selfie capture;
- face comparison;
- active/passive liveness records;
- PAD model integration;
- thresholds, evidence and Manual Review fallback.

Next outcomes:

- representative evaluation;
- attack coverage reporting;
- accessibility alternatives;
- provider replacement and fallback;
- device/capture integrity improvements.

### Result delivery — Implemented foundation

Current foundations:

- verification result API;
- signed webhooks;
- retry attempts;
- idempotency and request IDs;
- SDK and CLI access.

Next outcomes:

- signed result attestations;
- richer evidence/claim disclosure controls;
- end-to-end customer certification;
- stable event versioning.

## 8. Production readiness

Before representing IdentityCore as production-ready for sensitive deployments, complete and verify:

- independent security assessment;
- tenant isolation and authorization testing;
- provider egress and SSRF review;
- model evaluation and fairness analysis;
- backup and restore exercises;
- incident response and breach procedures;
- monitoring and alerting;
- key management and secret rotation;
- retention/deletion verification;
- provider and subprocessor governance;
- deployment-specific legal and compliance review;
- load, failure and recovery tests;
- pilot operating procedures.

## 9. Future workloads

### Planned platform directions

- reusable verified claims;
- age and eligibility assertions;
- registry-backed identity resolution;
- step-up and repeat identity checks;
- account recovery;
- deduplication;
- organizational identity;
- credential issuance and validation;
- employee, student, vendor and program eligibility workflows.

### Exploratory directions

- selective-disclosure credentials;
- identity wallet integration;
- cross-organization trust exchange;
- federated evidence and claim networks;
- privacy-preserving matching;
- national-scale identity infrastructure deployments.

These directions require separate product, security, legal and architectural decisions before becoming commitments.

## 10. Roadmap discipline

A roadmap item should advance at least one of these platform goals:

- provider neutrality;
- interoperability;
- security;
- privacy;
- auditability;
- tenant isolation;
- evidence quality and lineage;
- developer experience;
- operational resilience;
- workload reuse.

Features that reinforce a single hard-coded provider or workload at the expense of platform abstractions should be redesigned before implementation.
