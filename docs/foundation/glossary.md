# Glossary

## IdentityCore

**Version:** 1.0

---

## Purpose

This glossary defines the standard terminology used throughout IdentityCore.

All documentation, source code, APIs, database models, user interfaces, and discussions should use these terms consistently.

When introducing new concepts, this glossary should be updated before implementation.

---

## A

## Access Token

A short-lived token issued after successful authentication and used to authorize API requests.

---

## Actor

Any entity performing an action within IdentityCore.

Examples:

- Platform User
- Organization User
- API Client
- Verification Subject
- Internal Service

---

## API Client

A registered application that communicates with IdentityCore through the public REST API.

Each API Client has:

- Client ID
- Client Secret
- Scopes
- Rate limits
- Allowed networks

---

## Audit Event

An immutable record of a security-sensitive or business-critical action performed within the platform.

Examples:

- User login
- Verification created
- Manual decision recorded
- API key generated

---

## Authentication

The process of verifying the identity of an Actor.

---

## Authorization

The process of determining whether an authenticated Actor has permission to perform a specific action.

---

## B

## Biometric Data

Information derived from a person's biological characteristics for identity verification.

Examples:

- Face image
- Face embedding
- Selfie capture
- Liveness media

---

## Biometric Template

A mathematical representation of biometric features used for comparison.

A biometric template is **not** the original image.

---

## Background Worker

A service that processes asynchronous jobs outside the main request-response cycle.

IdentityCore uses Celery workers for this purpose.

---

## C

## Celery

The background task processing system used by IdentityCore.

---

## Consent

A recorded agreement by the Verification Subject permitting identity verification for a defined purpose.

---

## Consent Record

A permanent record of consent containing:

- Purpose
- Organization
- Policy version
- Timestamp
- Consent version
- Verification Subject confirmation

---

## Country Profile

A configuration describing the identity documents, rules, and localization for a particular country.

Example:

Ghana

Supported document types:

- National ID
- Passport
- Driver License
- Health ID

---

## D

## Decision Engine

The business component responsible for producing the final Verification Decision using evidence and Verification Policies.

The AI service never performs this responsibility.

---

## Document Capture

A digital image of one side of an Identity Document submitted during verification.

---

## Document Classification

The AI process that determines the generic type of an Identity Document.

Examples:

- National ID
- Passport
- Driver License

---

## Document Quality Check

An AI process that determines whether an uploaded document image is suitable for verification.

---

## E

## Embedding

See **Biometric Template**.

---

## Evidence

Technical information collected during verification.

Examples:

- Face match score
- OCR result
- Liveness result
- Document quality score

Evidence supports decisions but is not itself a decision.

---

## F

## Face Detection

The AI process of locating one or more faces within an image.

---

## Face Embedding

See **Biometric Template**.

---

## Face Match

The AI process of comparing two biometric templates to determine similarity.

---

## Face Match Score

A numerical similarity score produced by the face matching model.

Higher scores generally indicate greater similarity.

---

## G

## GraphQL

The internal query language used for IdentityCore dashboards.

GraphQL is not intended as the public integration API in Version 1.0.

---

## H

## Health Check

An endpoint used to determine whether a service is operating correctly.

---

## I

## Identity Document

An official document presented to prove identity.

Examples include:

- National ID
- Passport
- Driver License
- Voter ID
- Health ID

Country-specific names are handled by Country Profiles.

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

## M

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
