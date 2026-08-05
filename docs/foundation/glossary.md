# Glossary

## Purpose

This glossary defines key terminology used across IdentityCore documentation and implementation.

Terms are written to avoid circular definitions and to distinguish platform-level concepts from workload-specific capabilities.

---

## Application

A customer-facing service, website, mobile app, or integration that interacts with IdentityCore through APIs, SDKs, CLI, or hosted journeys.

## Workload

A business-purpose composition of IdentityCore platform primitives such as workflows, policies, capabilities, evidence, claims, and decisions.

Example: identity verification is the first workload built on the platform.

## Identity Infrastructure

Reusable software and operational capabilities that coordinate identity-related data, providers, evidence, privacy, and decision-making.

IdentityCore is vendor-neutral identity infrastructure.

## Identity Operating System

A conceptual layer that separates applications from provider-specific identity capabilities, offering stable orchestration, governance, and evidence services.

## Control Plane

The configuration and governance layer that manages tenants, organizations, projects, environments, workflows, policies, providers, access, and operational settings.

## Execution Plane

The runtime layer that executes workloads, invokes providers, normalizes evidence, evaluates policies, records decisions, and drives review and audit.

## Provider

A replaceable system or service that implements one or more capability contracts for IdentityCore.

## IdentityCore Managed Provider

A provider implementation operated by the IdentityCore deployment. It is a default provider implementation that is invoked through the same provider runtime boundary as external providers.

## Commercial Provider

An external vendor that supplies one or more identity-related capabilities behind IdentityCore capability contracts.

## Customer-hosted Provider

A provider implementation run inside the customer's own deployment, network, or controlled infrastructure.

## Government or Authoritative Provider

A registry, issuer, or authoritative source operated by a government or trusted authority that supplies identity, credential, or eligibility evidence.

## Provider Runtime

The execution boundary that resolves, secures, invokes, and normalizes provider capability calls for IdentityCore.

## Provider Adapter

A software layer that translates IdentityCore capability requests into provider-specific API or protocol interactions.

## Provider Registry

The configured set of provider records and capability declarations available to IdentityCore for a tenant, project, or environment.

## Provider Assignment

A binding that associates a capability with a selected provider for a supported scope.

## Provider Route

An ordered or conditional mapping that decides which provider implementation should be selected for a capability based on workflow, policy, context, or operational rules.

## Provider Check

An auditable record of a provider invocation, including the selected provider, capability, capability contract version, status, timestamps, normalized result, and safe diagnostics.

## Provider Attempt

An individual invocation or retry of a provider as part of a provider check lifecycle.

## Capability

A stable operation that IdentityCore requests from a provider, such as `document.ocr` or `biometric.liveness`.

## Capability Contract

A versioned definition of a capability's inputs, outputs, evidence requirements, error semantics, and normalized result schema.

## Capability Version

The version identifier of a capability contract.

## Evidence

Technical information collected during a workload execution that records what was observed, supplied, or produced.

## Raw Evidence

Original or provider-native material such as uploaded media, provider payloads, or registry responses.

## Normalized Evidence

A stable IdentityCore representation derived from raw evidence and provider output.

## Evidence Lineage

The directed references that show how evidence records were derived from earlier evidence, provider checks, or workflows.

## Evidence Grant

A short-lived authorization or reference that allows a provider to access the evidence needed to perform a capability.

## Claim

A normalized statement about a subject, organization, credential, or relationship that is linked to supporting evidence and policy.

## Extracted Claim

A candidate statement derived from raw or submitted evidence, such as OCR text extracted from a document.

## Provider-asserted Claim

A statement returned directly by a provider, such as a registry match or issuer assertion.

## Normalized Claim

A claim mapped into a stable IdentityCore schema.

## Derived Claim

A claim calculated from other claims and policy context.

## Policy-satisfied Claim

A claim whose status indicates it satisfies a policy requirement for a workload.

## Workflow

A versioned definition of ordered and conditional capability and review steps for a workload.

## Workflow Snapshot

An immutable record of the workflow version and configuration used by a particular execution.

## Policy

A versioned set of rules, thresholds, and constraints used to evaluate evidence and claims.

## Policy Snapshot

An immutable copy of the policy configuration used by a particular execution.

## Decision Engine

The component responsible for recording outcomes based on evidence, claims, workflow state, and policy.

## Decision Input Snapshot

An immutable record of the evidence, claims, workflow, and policy inputs used to create a decision.

## Manual Review

A governed human review activity for cases that require human judgment, uncertainty handling, or exceptional decision escalation.

## Maker-checker

A separation of duties pattern in which one reviewer proposes a decision and another reviewer approves it.

## Tenant

A logical isolation boundary for organizations, data, providers, and configuration.

## Organization

A customer entity that owns tenants, users, API clients, workflows, policies, providers, and identity operations.

## Project

A grouping within a tenant, often representing sandbox or production scope.

## Environment

A scoped execution context such as sandbox or production with separate credentials, configuration, and data boundaries.

## Subject

An individual or entity whose identity is being verified or asserted.

## Verification

A completed or in-progress identity verification operation.

## Verification Session

A short-lived session used by a subject during a verification workflow.

## IdentityCore SDK

A customer-facing SDK for integrating applications with IdentityCore APIs, workflows, evidence, decisions, and webhooks.

## Provider SDK

An integration contract or library used by provider implementers to connect a provider to IdentityCore's runtime.

---

## Note

Terms should be updated as the platform evolves, but the distinction between platform infrastructure and workload-specific capabilities must remain clear.

---

## Identity Provider

An external system responsible for authenticating users.

Future versions may integrate with enterprise identity providers.

---

## Idempotency

A property ensuring that repeating the same request produces the same result without unintended side effects.

---

## Internal Service

A backend service that is not directly accessible by external clients.

Example:

FastAPI AI Service.

---

## J

## Jurisdiction

A legal or regulatory region governing how data must be processed, retained, and protected.

Examples:

- Ghana
- Nigeria
- European Union

---

## L

## Liveness Check

An AI process that determines whether the Verification Subject is physically present rather than presenting a photograph, video, or other spoof.

---

## Liveness Score

A confidence score produced by the liveness detection model.

---

## Manual Review

A verification process performed by an authorized human reviewer when automated evidence is insufficient or inconclusive.

---

## Model Registry

The system that records AI model names, versions, and metadata used during processing.

---

## N

## National ID

A generic document type representing a government-issued national identity card.

Examples:

- Ghana Card
- National Identity Card (other jurisdictions)

---

## O

## Object Storage

A storage system used for large files such as:

- Document captures
- Selfie captures
- Liveness media

Examples include S3-compatible storage and Cloudflare R2.

---

## OCR

Optical Character Recognition.

The AI process of extracting machine-readable from an Identity Document.

---

## Organization

A customer using IdentityCore to perform identity verification.

Examples:

- Bank
- University
- Employer
- Government agency
- Hospital

---

## Organization User

A user belonging to an Organization who accesses the Organization Dashboard.

---

## P

## Platform Administrator

A privileged user responsible for administering the IdentityCore platform.

Platform Administrators are distinct from Organization Administrators.

---

## Platform User

Any authenticated user with access to IdentityCore dashboards.

Includes:

- Platform Administrators
- Organization Administrators
- Verification Officers

---

## Provider

An external service integrated into IdentityCore.

Examples:

- OCR provider
- KYC provider
- SMS provider
- Email provider

---

## Provider Adapter

A software layer that isolates IdentityCore from provider-specific implementations.

---

## Public ID

A prefixed ULID exposed through APIs.

Examples:

```id="ew7bb2"
ver_01...
org_01...
sub_01...
doc_01...
```

Public IDs are immutable and safe to expose externally.

---

## R

## Request ID

A unique identifier assigned to every request for tracing and debugging.

---

## REST API

The public integration interface exposed by IdentityCore.

---

## Risk Score

A calculated score representing the overall confidence or risk associated with a verification.

The Risk Score may combine:

- Face Match Score
- Liveness Score
- OCR confidence
- Document quality
- Fraud signals

---

## Role

A collection of permissions assigned to a Platform User.

Examples:

- Platform Administrator
- Organization Administrator
- Verification Officer

---

## S

## Selfie Capture

A photograph or video of the Verification Subject captured during the verification process.

---

## Service Layer

The application layer responsible for implementing business logic independently of API endpoints.

---

## Session

See **Verification Session**.

---

## STRIDE

A structured threat modeling framework covering:

- Spoofing
- Tampering
- Repudiation
- Information Disclosure
- Denial of Service
- Elevation of Privilege

---

## T

## Tenant

A logical isolation boundary representing one Organization's data within IdentityCore.

Tenant isolation is mandatory.

---

## Tenant Isolation

The security principle ensuring one Organization cannot access another Organization's data.

---

## Threshold

A configurable value used by the Decision Engine to interpret AI evidence.

Examples:

- Face match threshold
- Liveness threshold
- Document quality threshold

---

## U

## ULID

Universally Unique Lexicographically Sortable Identifier.

IdentityCore uses prefixed ULIDs as Public IDs.

---

## V

## Verification

A single identity verification request initiated by an Organization.

A Verification contains:

- Verification Subject
- Verification Policy
- Verification Session
- Evidence
- Decision
- Audit Events

---

## Verification Decision

The final business outcome of a Verification.

Examples:

- Verified
- Rejected
- Manual Review Required

Verification Decisions are produced by the Decision Engine, not by AI models.

---

## Verification Officer

An authorized Organization User responsible for reviewing verification cases.

---

## Verification Policy

A configurable set of rules controlling how a Verification should be processed.

Examples:

- Required document types
- Face match threshold
- Liveness threshold
- Retention periods

---

## Verification Portal

The frontend application used by the Verification Subject to complete the verification process.

---

## Verification Session

A secure, time-limited session allowing a Verification Subject to complete a Verification.

---

## Verification Subject

The individual whose identity is being verified.

This term replaces generic labels such as "end user" or "customer" because it accurately reflects the platform's purpose.

---

## W

## Webhook

An HTTP callback sent automatically when important events occur.

Examples:

- Verification completed
- Verification rejected
- Manual review required

---

## Webhook Endpoint

A registered destination that receives webhook events from IdentityCore.

---

## Standard Terminology Rules

Throughout IdentityCore:

Use:

- Verification Subject
- Identity Document
- Verification Decision
- Public ID
- Tenant
- Organization
- Verification Policy
- Audit Event
- Provider Adapter

Avoid:

- End User
- Customer Photo
- User Photo
- Ghana Card as a platform-wide term
- Internal database IDs in APIs

Country-specific terminology should be handled through Country Profiles rather than embedded in business logic.

---

## Final Principle

Every technical, business, and user-facing component of IdentityCore should use the terminology defined in this glossary.

A shared vocabulary reduces ambiguity, improves communication, simplifies implementation, and ensures consistency across documentation, APIs, source code, and future integrations.
