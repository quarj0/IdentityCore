# Domain Model

## IdentityCore

**Version:** 1.0

---

## Purpose

This document defines the core business concepts used across IdentityCore.

The goal of this document is to establish a shared language for product, engineering, security, compliance, and business discussions. Every service, database table, API endpoint, dashboard screen, and future integration should use this language consistently.

IdentityCore uses domain-driven design principles. The platform architecture should reflect the business domain rather than forcing the business into technical terminology.

---

## Core Principle

IdentityCore is an identity infrastructure platform.

The platform does not simply process users, photos, or documents. It manages identity verification workflows involving organizations, verification subjects, documents, biometric evidence, consent, risk, decisions, and auditability.

---

## Ubiquitous Language

The following terms must be used consistently across the platform.

---

## Platform

## Definition

The Platform refers to the complete IdentityCore system, including APIs, dashboards, verification flows, AI services, audit logs, infrastructure, and integrations.

## Purpose

The Platform provides secure identity verification capabilities to organizations.

## Business Rules

- The Platform may serve multiple organizations.
- The Platform must enforce tenant isolation.
- The Platform must maintain security, auditability, and privacy by design.

---

## Organization

## Definition

An Organization is a customer, institution, agency, or business that uses IdentityCore to verify identities.

Examples include:

- School
- University
- Employer
- Hospital
- Event organizer
- Security company
- Financial institution
- Government agency

## Purpose

Organizations create and manage verification workflows for Verification Subjects.

## Relationships

- An Organization has Users.
- An Organization has API Clients.
- An Organization creates Verifications.
- An Organization owns its verification data.
- An Organization may have one or more Workspaces in future versions.

## Business Rules

- Organization data must be isolated from other organizations.
- Organization users may only access data permitted by their role.
- Organization settings may define branding, allowed Document Types, retention rules, and verification policies.
- Platform settings remain separate and govern system defaults such as security policy, service endpoints, storage, and feature flags.

---

## Tenant

## Definition

A Tenant is the isolated technical boundary representing an Organization inside the Platform.

## Purpose

The Tenant ensures that each Organization's data, configuration, users, API keys, and verification records remain separated.

## Relationship to Organization

In Version 1.0, one Organization maps to one Tenant.

Future versions may support:

- One Organization with multiple Tenants
- Parent-child organizations
- Regional branches
- Government agency hierarchies

## Business Rules

- Every Verification belongs to a Tenant.
- Every Organization User belongs to a Tenant.
- Every API Client belongs to a Tenant.
- Tenant context must be enforced on every request.

---

## Platform User

## Definition

A Platform User is a person who logs into IdentityCore to manage or operate the platform.

Platform Users include:

- Platform Administrator
- Organization Administrator
- Verification Officer
- Support User
- Compliance Reviewer

## Purpose

Platform Users manage organizations, configure verification workflows, review verification results, and monitor audit records.

## Business Rules

- A Platform User must authenticate before accessing protected resources.
- A Platform User must be assigned roles and permissions.
- A Platform User is different from a Verification Subject.

---

## Verification Subject

## Definition

A Verification Subject is the individual whose identity is being verified.

Examples include:

- Customer
- Student
- Employee
- Visitor
- Patient
- Event participant
- Citizen

## Purpose

The Verification Subject provides identity evidence such as documents, selfies, biometric captures, and consent.

## Business Rules

- A Verification Subject must give consent before verification begins.
- A Verification Subject may be associated with multiple Verifications over time.
- The platform should avoid storing unnecessary personal data about the Verification Subject.
- The Verification Subject is not automatically a Platform User.

---

## Verification

## Definition

A Verification is the complete process of confirming a Verification Subject's identity.

It includes consent, document capture, selfie capture, liveness detection, face matching, risk assessment, and final decision.

## Purpose

The Verification is the central workflow object in IdentityCore.

## Lifecycle Statuses

- Created
- Pending Consent
- In Progress
- Awaiting Document
- Awaiting Selfie
- Processing
- Manual Review Required
- Verified
- Rejected
- Expired
- Cancelled
- Failed

## Relationships

- A Verification belongs to one Tenant.
- A Verification belongs to one Organization.
- A Verification involves one Verification Subject.
- A Verification may contain one or more Identity Documents.
- A Verification may contain one or more Selfie Captures.
- A Verification may contain one or more Liveness Checks.
- A Verification may contain one or more Face Matches.
- A Verification produces one Verification Decision.
- A Verification generates Audit Events.

## Business Rules

- A Verification must not proceed without valid consent.
- A Verification must have an expiration time.
- A completed Verification must have a final decision.
- A Verification should be traceable from creation to final outcome.
- Sensitive verification evidence should follow retention policies.

---

## Verification Session

## Definition

A Verification Session is a time-bound interaction where a Verification Subject completes the required steps for a Verification.

## Purpose

The Verification Session manages the subject-facing journey.

## Examples

- Opening a verification link
- Accepting consent
- Uploading an identity document
- Capturing a selfie
- Completing a liveness challenge

## Business Rules

- A Verification Session must expire.
- A Verification Session must be tied to one Verification.
- A Verification Session should not expose internal organization data.
- A Verification Session should be resumable only when allowed by policy.

---

## Identity Document

## Definition

An Identity Document is a document submitted as evidence of identity.

Examples include:

- National ID
- Passport
- Driver License
- Voter ID
- Health ID
- Residence Permit
- Student ID
- Employee ID

## Purpose

Identity Documents provide biographical and visual evidence used during verification.

## Business Rules

- Every Identity Document must have a Document Type.
- Every Identity Document should be associated with a country or jurisdiction when applicable.
- Raw document images should be retained only according to policy.
- Extracted document data should be minimized.

---

## Document Type

## Definition

A Document Type is a generic classification of an Identity Document.

Supported Document Types for Version 1.0:

- National ID
- Passport
- Driver License
- Voter ID
- Health ID
- Residence Permit
- Student ID
- Employee ID
- Other

## Purpose

Document Types prevent the platform from hardcoding country-specific document names.

## Business Rules

- The platform must use generic Document Types internally.
- Country-specific document names must be configured through Country Profiles or Provider Adapters.
- Example: Ghana Card should map to National ID under the Ghana Country Profile.
- Example: NHIS Card should map to Health ID under the Ghana Country Profile.

---

## Country Profile

## Definition

A Country Profile defines country-specific identity rules, document names, issuing authorities, document formats, and supported providers.

## Purpose

Country Profiles allow IdentityCore to expand across countries without changing core platform logic.

## Examples

Ghana Country Profile:

- National ID → Ghana Card
- Health ID → NHIS Card
- Driver License → DVLA Driver License
- Voter ID → Electoral Commission Voter ID

## Business Rules

- Country-specific behavior must live in Country Profiles or Provider Adapters.
- The core platform must not hardcode country-specific document names.
- Each Organization should have a default Country Profile.

---

## Jurisdiction

## Definition

A Jurisdiction is the legal or administrative region under which a verification operates.

Examples include:

- Ghana
- Nigeria
- Kenya
- Rwanda
- European Union
- Specific government agency jurisdiction

## Purpose

Jurisdiction determines applicable compliance rules, data retention requirements, identity providers, and allowed document types.

## Business Rules

- Every Organization should be associated with a Jurisdiction.
- Every Verification should inherit a Jurisdiction from the Organization unless overridden.
- Compliance policies may vary by Jurisdiction.

---

## Document Capture

## Definition

A Document Capture is the submitted image, scan, or digital representation of an Identity Document.

## Purpose

Document Captures provide raw evidence for document processing, OCR, classification, and face extraction.

## Business Rules

- A Document Capture must belong to an Identity Document.
- A Document Capture may include front image, back image, or both.
- Document Capture quality must be validated.
- Document Capture storage must be encrypted.
- Document Captures must follow retention rules.

---

## Selfie Capture

## Definition

A Selfie Capture is an image or video of the Verification Subject captured during the verification process.

## Purpose

Selfie Captures provide biometric evidence for liveness detection and face matching.

## Business Rules

- A Selfie Capture must belong to a Verification.
- A Selfie Capture should be captured during a valid Verification Session.
- A Selfie Capture must pass quality checks.
- A Selfie Capture must follow biometric data handling rules.

---

## Biometric Template

## Definition

A Biometric Template is a mathematical representation of biometric data, such as a face embedding.

## Purpose

Biometric Templates enable comparison without repeatedly processing raw biometric images.

## Business Rules

- Biometric Templates are sensitive data.
- Biometric Templates must be encrypted at rest.
- Biometric Templates must not be exposed through public APIs.
- Biometric Templates should be deleted according to retention policy unless long-term storage is explicitly required and legally permitted.

---

## Liveness Check

## Definition

A Liveness Check determines whether the Verification Subject is physically present and not using a spoofing method such as a printed photo, screen replay, mask, or deepfake.

## Purpose

Liveness Checks reduce impersonation and presentation attacks.

## Types

- Passive Liveness
- Active Liveness

## Business Rules

- A Liveness Check must produce a confidence score.
- Failed liveness may cause rejection or manual review.
- Liveness evidence must be retained only according to policy.

---

## Face Match

## Definition

A Face Match compares facial evidence from two sources, usually a Selfie Capture and a document portrait.

## Purpose

Face Matching helps determine whether the Verification Subject matches the submitted Identity Document.

## Outputs

- Match score
- Confidence level
- Match result
- Model version
- Processing timestamp

## Business Rules

- A Face Match must not be the only basis for high-impact decisions.
- Face Match thresholds should be configurable by Organization policy.
- Face Match results should be explainable at a high level.
- Face Match model versions must be recorded for auditability.

---

## Consent

## Definition

Consent is the Verification Subject's explicit agreement to participate in a verification process.

## Purpose

Consent establishes lawful and transparent participation in identity verification.

## Required Consent Metadata

- Consent timestamp
- Verification purpose
- Organization requesting verification
- Data being collected
- Data retention period
- Policy version
- Subject agreement record

## Business Rules

- Consent must be captured before verification begins.
- Consent must be auditable.
- Consent language must be understandable.
- Consent should be tied to a specific Verification.
- Withdrawal of consent must be handled according to applicable law and policy.

---

## Verification Policy

## Definition

A Verification Policy defines the rules used to determine how a Verification should be performed.

## Examples

- Required document types
- Required liveness level
- Face match threshold
- Manual review threshold
- Verification expiry period
- Retention period
- Allowed countries
- Webhook events

## Purpose

Verification Policies allow Organizations to configure verification workflows without changing platform code.

## Business Rules

- Every Verification must use a Verification Policy.
- Verification Policies may vary by Organization.
- Policy versions must be recorded during verification.

---

## Verification Decision

## Definition

A Verification Decision is the final outcome of a Verification.

## Possible Outcomes

- Verified
- Rejected
- Manual Review Required
- Expired
- Cancelled
- Failed

## Purpose

The Verification Decision summarizes the outcome of all verification checks.

## Business Rules

- A completed Verification must have one final Verification Decision.
- A Verification Decision must include reasons or supporting evidence.
- Manual decisions must record the Verification Officer responsible.
- Decision rules must be tied to the Verification Policy version used.

---

## Manual Review

## Definition

Manual Review is a process where a Verification Officer reviews a Verification that cannot be automatically approved or rejected.

## Purpose

Manual Review provides human oversight for uncertain, sensitive, or high-risk cases.

## Business Rules

- Manual Review must be assigned to authorized Verification Officers.
- Manual Review actions must be logged.
- Manual Review decisions must include reason codes.
- Manual Review should not expose unnecessary sensitive data.

---

## Risk Assessment

## Definition

A Risk Assessment evaluates fraud, inconsistency, or trust signals associated with a Verification.

## Examples of Risk Signals

- Failed liveness
- Low face match score
- Poor document quality
- Duplicate verification attempt
- Suspicious device
- Unusual location
- Repeated failed attempts

## Purpose

Risk Assessment helps determine whether a Verification should be approved, rejected, or sent to manual review.

## Business Rules

- Risk scores must be explainable.
- Risk thresholds must be configurable.
- Risk Assessment should assist decisions, not act as the sole authority for sensitive outcomes.

---

## Audit Event

## Definition

An Audit Event is an immutable record of an important action or system event.

## Examples

- User login
- Verification created
- Consent accepted
- Document uploaded
- Liveness completed
- Face match completed
- Decision made
- API key generated
- Webhook delivered
- Admin setting changed

## Purpose

Audit Events provide transparency, accountability, forensic traceability, and compliance evidence.

## Business Rules

- Audit Events must be immutable.
- Audit Events must include actor, action, timestamp, tenant, IP/device context where available, and target resource.
- Sensitive fields must be masked.
- Audit Events must not be deleted casually.

---

## API Client

## Definition

An API Client is an application or system authorized to access IdentityCore APIs on behalf of an Organization.

## Purpose

API Clients allow external systems to create verifications, retrieve results, and receive webhook events.

## Business Rules

- API Clients belong to a Tenant.
- API Clients must use secure credentials.
- API Clients may have scoped permissions.
- API Client activity must be rate limited and audited.

---

## Webhook Event

## Definition

A Webhook Event is a notification sent to an Organization's system when an important verification event occurs.

## Examples

- verification.created
- verification.consent_accepted
- verification.processing
- verification.manual_review_required
- verification.verified
- verification.rejected
- verification.expired

## Purpose

Webhook Events allow external systems to react to verification progress and outcomes.

## Business Rules

- Webhook Events must be signed.
- Webhook delivery attempts must be logged.
- Failed webhooks should be retried.
- Webhook payloads must avoid unnecessary sensitive data.

---

## Notification

## Definition

A Notification is a message sent to a Platform User or Verification Subject.

## Examples

- Verification link email
- Verification completed email
- Manual review assigned notification
- Security alert

## Purpose

Notifications keep relevant parties informed about verification activity.

## Business Rules

- Notifications must respect tenant configuration.
- Notifications must avoid exposing unnecessary sensitive information.
- Security-related notifications should be prioritized.

---

## Provider

## Definition

A Provider is an external or internal service used to perform part of a verification.

Examples include:

- Document intelligence provider
- Face recognition provider
- Liveness provider
- Identity database provider
- Government identity authority
- Sanctions or watchlist provider

## Purpose

Providers allow IdentityCore to connect to different verification technologies and data sources.

## Business Rules

- Provider integrations must be abstracted through adapters.
- Provider responses must be normalized.
- Provider credentials must be securely stored.
- Provider usage must be logged.

---

## Provider Adapter

## Definition

A Provider Adapter is a software component that translates IdentityCore requests into provider-specific API calls and normalizes provider responses.

## Purpose

Provider Adapters prevent external provider differences from leaking into the core platform.

## Business Rules

- The core platform must depend on normalized provider interfaces, not provider-specific logic.
- Provider Adapters should be replaceable.
- Provider failures must be handled safely.
- Provider response metadata must be stored for auditability without storing unnecessary sensitive data.

---

## Role

## Definition

A Role is a named set of permissions assigned to a Platform User.

## Examples

- Platform Administrator
- Organization Administrator
- Verification Officer
- Compliance Reviewer
- Support User
- Developer

## Purpose

Roles simplify access control.

## Business Rules

- Roles must be scoped to a Tenant unless they are platform-level roles.
- Roles should follow least privilege.
- Role changes must be audited.

---

## Permission

## Definition

A Permission is a specific ability granted to a Role or User.

## Examples

- create_verification
- view_verification
- review_verification
- manage_api_keys
- view_audit_logs
- manage_users
- configure_policies

## Purpose

Permissions enforce granular access control.

## Business Rules

- Permissions must be checked server-side.
- Sensitive permissions may require additional approval or MFA.
- Permission checks must include tenant context.

---

## Data Retention Policy

## Definition

A Data Retention Policy defines how long different categories of data are stored.

## Purpose

Retention policies reduce privacy risk and support compliance.

## Examples

- Delete raw document captures after 30 days.
- Delete selfie captures after 30 days.
- Retain audit metadata for 7 years.
- Retain verification result metadata for business reporting.

## Business Rules

- Every Organization must have a retention policy.
- Retention policies must comply with jurisdiction requirements.
- Deletion must be auditable.

---

## Evidence

## Definition

Evidence refers to any data used to support a Verification Decision.

Examples include:

- Identity Document
- Document Capture
- Selfie Capture
- Liveness Check
- Face Match
- Provider Check
- Risk Assessment

## Purpose

Evidence provides traceability for why a Verification Decision was made.

## Business Rules

- Evidence must be linked to a Verification.
- Evidence must be protected based on sensitivity.
- Evidence should be minimized and retained only as needed.

---

## Provider Check

## Definition

A Provider Check is the result of calling a Provider during a Verification.

## Examples

- Document OCR check
- Face match provider check
- Liveness provider check
- Government identity lookup
- Watchlist check

## Purpose

Provider Checks record external or internal processing outcomes.

## Business Rules

- Provider Checks must record provider name, provider reference, status, timestamp, and normalized result.
- Raw provider payloads should be stored only when necessary and safely redacted.
- Failed Provider Checks should not expose provider internals to Verification Subjects.

---

## Business Object Relationships

At a high level:

```text
Organization
└── Tenant
    ├── Platform Users
    ├── Roles
    ├── Permissions
    ├── API Clients
    ├── Verification Policies
    └── Verifications
        ├── Verification Subject
        ├── Verification Session
        ├── Consent
        ├── Identity Documents
        │   └── Document Captures
        ├── Selfie Captures
        ├── Liveness Checks
        ├── Face Matches
        ├── Provider Checks
        ├── Risk Assessment
        ├── Evidence
        ├── Verification Decision
        └── Audit Events
```

---

## Naming Rules

The following naming rules must be followed across code, APIs, documentation, and user interfaces.

## Use

- Verification Subject
- Identity Document
- Document Type
- Selfie Capture
- Liveness Check
- Face Match
- Verification Decision
- Audit Event
- Organization
- Tenant
- Provider Adapter

## Avoid

- End User
- Customer photo
- User document
- Face scan
- Ghana Card as a core platform term
- NIA Service as a core platform service name
- Hardcoded country-specific identifiers in core logic

Country-specific names may appear in Country Profiles, Provider Adapters, UI labels, and integration documentation.

---

## Country-Specific Rule

IdentityCore must never hardcode country-specific business logic into the core platform.

Country-specific rules, document names, issuing authorities, formats, validation rules, and integrations must be implemented through:

- Country Profiles
- Jurisdiction Policies
- Provider Adapters
- Configuration

---

## Version 1.0 Domain Boundary

Version 1.0 includes:

- Organizations
- Tenants
- Platform Users
- Verification Subjects
- Verifications
- Verification Sessions
- Identity Documents
- Document Types
- Document Captures
- Selfie Captures
- Liveness Checks
- Face Matches
- Consent
- Verification Policies
- Verification Decisions
- Manual Review
- Risk Assessment
- Audit Events
- API Clients
- Webhook Events
- Providers
- Provider Adapters

Version 1.0 excludes:

- Government database ownership
- Criminal records
- Immigration intelligence
- Fingerprint recognition
- Iris recognition
- Digital wallets
- National identity issuance
- Centralized citizen database
- Law enforcement surveillance workflows

---

## Final Principle

The domain model exists to keep IdentityCore focused.

Every technical component must serve a clearly defined business concept. If a proposed feature cannot be mapped to a domain concept in this document, the concept must either be added intentionally or the feature should not be built.
