# IdentityCore Vision

## Vision statement

IdentityCore is building the vendor-neutral identity infrastructure on which governments, businesses, institutions, and digital platforms can establish trust without being locked into one identity-verification vendor.

Identity verification is the first workload built on the platform. It proves the platform through real document, biometric, policy, evidence, review, privacy, and audit flows, but it is not the boundary of IdentityCore.

The long-term vision is for IdentityCore to become a trusted identity operating layer for Africa and other regions: a common platform through which organizations can compose managed capabilities, commercial providers, government registries, customer-hosted services, and supporting infrastructure behind stable APIs and governance controls.

## Mission

To give organizations secure, privacy-preserving, interoperable, and auditable infrastructure for building identity and digital-trust services while giving individuals greater transparency and control over how their evidence and identity data are used.

## The problem

Digital identity is fragmented.

Organizations frequently integrate separate products for:

- document capture and verification;
- OCR and field extraction;
- face comparison and liveness;
- government or authoritative registries;
- fraud and risk signals;
- consent and privacy operations;
- Manual Review;
- storage and encryption;
- audit, compliance, and result delivery.

Each product brings different APIs, data formats, evidence semantics, pricing, country support, operational behavior, and compliance boundaries. Replacing a provider can require rewriting applications and losing historical consistency.

The result is vendor lock-in, duplicated integration work, weak evidence lineage, inconsistent decisions, poor portability, and limited organizational control.

## The IdentityCore approach

IdentityCore provides common infrastructure around identity capabilities rather than insisting that every capability be implemented by IdentityCore itself.

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
 workflows/policies        evidence and claims
 providers/privacy         decision engine
 configuration             manual review/audit
                    |
                    v
                 Providers
```

Providers may include:

- IdentityCore Managed Providers;
- commercial IDV vendors;
- specialist OCR, biometric, authenticity, fraud, or risk vendors;
- government and authoritative registries;
- customer-hosted services;
- storage providers;
- KMS/HSM providers;
- messaging and supporting infrastructure.

IdentityCore coordinates these capabilities through workflows, policies, evidence contracts, decisions, privacy controls, and audit records.

## Identity Operating System

The Identity Operating System concept describes IdentityCore's role as the reusable coordination layer for identity workloads.

Like an operating system separates applications from hardware-specific details, IdentityCore separates identity workloads from provider-specific APIs.

The platform supplies:

- tenant, project, and environment isolation;
- APIs, SDKs, CLI, webhooks, and hosted user journeys;
- Workflow Engine;
- Policy Engine;
- Provider Runtime;
- capability contracts;
- evidence provenance and lineage;
- claims foundations;
- Decision Engine;
- Manual Review and maker-checker controls;
- consent, retention, export, deletion, and legal-hold controls;
- tamper-evident audit and operational observability.

A workload composes these primitives for a particular purpose.

## Workload one: identity verification

Identity verification is the first working workload because it exercises the platform's hardest trust boundaries:

- obtaining consent;
- collecting sensitive evidence;
- selecting document and biometric capabilities;
- invoking providers;
- normalizing provider results;
- applying policies;
- making or reviewing decisions;
- delivering signed outcomes;
- retaining and deleting evidence responsibly;
- preserving a complete audit trail.

The verification workload currently includes foundations for document capture, quality, classification, OCR, face comparison, active and passive liveness, presentation attack detection, workflows, policies, Manual Review, privacy operations, webhooks, and SDK integration.

IdentityCore should continue improving this workload without allowing verification-specific assumptions to become permanent platform constraints.

## Platform capabilities

### Control Plane

Organizations configure and govern identity services through:

- organizations and tenants;
- projects and sandbox/production environments;
- users, roles, MFA, API clients, and scopes;
- versioned workflows, templates, and policies;
- provider registration and assignments;
- consent purposes;
- retention and privacy rules;
- audit, webhook, and operational configuration.

### Execution Plane

The Execution Plane:

- accepts an identity operation;
- loads immutable workflow and policy versions;
- determines required evidence and claims;
- invokes capabilities through the Provider Runtime;
- normalizes provider output;
- applies policy and risk rules;
- requests additional evidence or Manual Review;
- persists decision inputs and outcomes;
- emits audit events and signed result notifications.

### Provider Runtime

The Provider Runtime allows replaceable capability providers to participate behind stable contracts.

It is responsible for selection, invocation, authentication, signing, idempotency, timeout handling, normalization, redaction, observability, and deterministic failure semantics.

IdentityCore Managed Providers use this boundary rather than bypassing it.

### Evidence and claims

Providers produce evidence. Evidence retains provenance, capability, provider, model, schema, confidence, timestamps, integrity, retention, and lineage.

Claims are normalized statements derived from or supported by evidence and policy. A claim is not trusted merely because one provider returned it.

IdentityCore's evidence foundation is implemented across provider checks, document and biometric records, reports, decisions, and audit events. A generalized reusable Claims Engine remains an evolving platform capability.

### Workflow, policy, and decisions

Workflows define what must happen. Policies define what evidence is required and how it should be evaluated. The Decision Engine records the outcome and the versioned inputs used to reach it.

Provider outputs are not final business decisions. Authorized organizations remain responsible for the consequences of the outcomes they use.

### Manual Review

Manual Review is a first-class platform path for uncertainty, unsupported evidence, high-impact cases, and maker-checker governance.

Human decisions remain scoped, reasoned, auditable, and subject to policy and privacy controls.

## Managed providers

IdentityCore operates managed implementations for selected capabilities, currently including areas such as:

- document quality;
- document classification;
- OCR and field extraction;
- face detection and comparison;
- liveness and presentation attack detection;
- model metadata reporting.

These managed services provide useful defaults and accelerate deployment. They do not receive privileged contracts and must be replaceable by other conforming providers.

IdentityCore's long-term value must not depend on one OCR engine, biometric model, or vendor.

## Future workloads

The same platform primitives may support:

- reusable verified claims;
- selective age or eligibility assertions;
- registry-backed identity resolution;
- digital credential issuance and validation;
- step-up identity checks;
- repeat authentication and account recovery;
- deduplication;
- employee, student, vendor, and organizational identity;
- healthcare, education, financial, and public-service workflows;
- program-specific eligibility and trust processes.

These are platform directions, not claims that every workload is implemented today.

## Core principles

### Vendor neutrality

Applications should integrate with IdentityCore rather than depend directly on one provider's proprietary workflow and result format.

### Privacy by design

IdentityCore should collect only the evidence required for a declared purpose, use least-privilege access, apply retention and deletion controls, and make sensitive processing auditable.

### Security first

Tenant isolation, environment isolation, strong authentication, secure API credentials, signed messages, replay resistance, encryption, upload validation, and append-only audit are product requirements.

### Evidence before decisions

AI, registries, risk systems, and human reviewers contribute evidence. Policies and authorized decision processes determine outcomes.

### Interoperability

IdentityCore should integrate with existing government, enterprise, financial, healthcare, education, and specialist provider ecosystems rather than attempt to replace every system.

### Data ownership and portability

Organizations should retain meaningful control over their integrations, evidence lifecycle, provider choices, deployment boundaries, and future storage and key-management options.

### Explainability and auditability

An identity outcome should be traceable to the workflow, policy, providers, evidence, claims, reviewer actions, decision inputs, and delivery events involved.

### Country-agnostic core

Country and document support should be additive through definitions, capabilities, providers, and policy—not hardcoded into core business logic.

### Honest maturity

IdentityCore should distinguish implemented capabilities, foundations, partial functionality, planned work, and exploratory direction. Vision must not be presented as production completeness.

## Target users

IdentityCore is intended for organizations that need to establish trust while controlling their provider and infrastructure choices, including:

- government agencies and public-service platforms;
- financial institutions and fintechs;
- healthcare organizations;
- educational institutions;
- telecommunications companies;
- employers and workforce platforms;
- technology companies and SaaS providers;
- enterprise software vendors;
- event, marketplace, and mobility platforms;
- identity, risk, registry, and infrastructure providers.

## Success measures

IdentityCore will be successful when organizations can:

- integrate once and change providers without redesigning their applications;
- compose identity capabilities into governed workflows;
- understand the evidence behind every decision;
- operate across countries and document types without hardcoded core logic;
- control retention, deletion, access, and audit;
- deploy managed, commercial, government, or customer-hosted capabilities;
- build multiple trust workloads on the same platform primitives.

Long-term success should be measured not only by verification volume, but by:

- the number of workloads built on IdentityCore;
- the diversity of conforming providers;
- provider portability;
- evidence and claim reuse under policy;
- reduction in integration duplication;
- privacy and audit outcomes;
- operational reliability and trust.

## Boundaries

IdentityCore should not become:

- a centralized citizen database;
- a mass-surveillance platform;
- an autonomous authority for high-impact decisions;
- a system that exposes biometric templates publicly;
- a platform that stores raw evidence indefinitely;
- a product locked to one country, model, provider, or cloud;
- a marketplace that claims providers are certified without conformance and assurance.

## Current direction

The current repository already contains meaningful foundations for the vision:

- multi-tenancy and environment isolation;
- versioned workflows and policies;
- adapter-backed provider execution;
- secure HTTP provider calls and signed messages;
- normalized and versioned results;
- document and biometric managed providers;
- immutable decision snapshots;
- Manual Review and maker-checker decisions;
- subject export and deletion workflows;
- legal holds and retention cleanup;
- tamper-evident audit events;
- REST, GraphQL, SDKs, CLI, developer portal, and hosted verification applications.

Important gaps remain in advanced routing, provider conformance, reusable claims, tenant-owned storage, KMS/HSM integration, broad country coverage, and production assurance.

## Final statement

IdentityCore begins with identity verification, but its destination is broader identity infrastructure.

Its purpose is not to become another closed verification vendor. Its purpose is to provide the durable contracts—workflows, policies, providers, evidence, claims, decisions, privacy, and audit—through which organizations can build trusted digital services while retaining choice and control.
