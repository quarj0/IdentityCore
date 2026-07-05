# Roadmap

## IdentityCore

**Version:** 1.0

---

## Purpose

This document defines the product and engineering roadmap for IdentityCore.

The roadmap exists to prevent scope creep, guide development priorities, and ensure the platform grows from a focused MVP into a larger identity infrastructure platform without losing architectural discipline.

---

## Roadmap Principle

IdentityCore must start small, secure, and useful.

The first version should not attempt to become a government identity platform, national registry, or full biometric intelligence system.

The platform should first prove that it can reliably verify a person's identity using document capture, selfie capture, liveness detection, face matching, consent, audit logs, and secure APIs.

---

## Phase 0: Foundation

Status: In Progress

Purpose:

Define the product, architecture, and engineering rules before implementation begins.

Deliverables:

* Vision
* Product Requirements Document
* Domain Model
* System Architecture
* Database Design
* API Specification
* Security
* Compliance
* AI Design
* Deployment
* Threat Model
* Coding Standards
* Testing Strategy
* Architecture Decision Records

Success criteria:

* Project scope is clear.
* MVP boundaries are defined.
* Core terminology is consistent.
* Architecture supports future expansion.
* Security and compliance expectations are documented.

---

## Phase 1: Core Platform MVP

Purpose:

Build the first working version of IdentityCore.

Core features:

* Django backend
* FastAPI AI service
* PostgreSQL database
* Redis
* Celery workers
* Multi-tenant architecture
* Platform Users
* Organizations
* Tenants
* Roles and permissions
* API Clients
* Verification Policies
* Verification Subjects
* Verifications
* Verification Sessions
* Consent Records
* Audit Events
* Webhooks

Success criteria:

* Organization can create an account.
* Organization can generate API credentials.
* Organization can create a Verification.
* Verification Subject can open a secure Verification Session.
* Consent can be captured.
* Audit logs are generated.
* Webhooks can be delivered.

---

## Phase 2: Identity Verification MVP

Purpose:

Deliver the first end-to-end verification workflow.

Core features:

* Document upload
* Document type selection
* Country Profile support
* Document quality checks
* OCR processing
* Selfie capture
* Face detection
* Face matching
* Passive liveness check
* Verification Decision Engine
* Manual Review
* Verification results API

Success criteria:

* Verification Subject can complete a full verification.
* Identity Document and Selfie Capture can be processed.
* Face matching produces a score.
* Liveness produces a score.
* Verification Policy determines the outcome.
* Manual Review handles uncertain cases.
* Organization receives webhook result.

---

## Phase 3: Dashboard and Developer Experience

Purpose:

Make the platform usable for organizations and developers.

Core features:

* Organization Dashboard
* Verification list
* Verification details
* Manual Review screen
* API Client management
* Webhook management
* Verification Policy management
* Basic reports
* Developer documentation
* API examples
* Postman collection

Success criteria:

* Organization Administrator can manage verification workflows.
* Verification Officer can review cases.
* Developer can integrate using REST APIs.
* API Client can test webhooks.
* Organization can view audit logs.

---

## Phase 4: Production Readiness

Purpose:

Prepare IdentityCore for real pilots.

Core features:

* Production deployment
* Monitoring
* Error tracking
* Backup strategy
* Retention cleanup
* Security headers
* Rate limiting
* MFA
* API key rotation
* Signed webhooks
* Idempotency
* Audit hardening
* Basic incident response process

Success criteria:

* Platform can safely support pilot organizations.
* Sensitive media is protected.
* Audit logs are reliable.
* Backups are tested.
* Webhook delivery is resilient.
* Security controls are enabled.

---

## Phase 5: Pilot Program

Purpose:

Test IdentityCore with real organizations in controlled environments.

Target pilot customers:

* Schools
* Universities
* Hostels
* Employers
* Event organizers
* Security companies
* Training institutions

Pilot features:

* Tenant onboarding
* Custom organization branding
* Verification links
* API integration
* Manual review
* Reports
* Support process

Success criteria:

* At least one organization completes real verification workflows.
* Verification completion rate is measured.
* Manual review rate is measured.
* False rejection feedback is collected.
* Product gaps are identified.
* Security and operational issues are documented.

---

## Phase 6: Provider and Country Expansion

Purpose:

Expand document and identity verification coverage.

Core features:

* More Country Profiles
* More local document mappings
* Provider Adapter improvements
* Optional third-party KYC provider integration
* Passport support
* Driver License support
* Health ID support
* Voter ID support
* Better OCR templates
* Provider fallback strategy

Success criteria:

* Platform supports multiple document types.
* Platform can add a country without core code changes.
* Provider adapters can be replaced or extended.
* Country-specific logic remains outside the core platform.

---

## Phase 7: Advanced Risk and Fraud

Purpose:

Improve fraud detection and decision support.

Core features:

* Duplicate verification detection
* Device fingerprinting
* Suspicious IP/network detection
* Repeated failure detection
* Risk scoring improvements
* Manual review prioritization
* Fraud reports
* Provider risk signals

Success criteria:

* Risk scores are explainable.
* High-risk cases are prioritized.
* Fraud signals improve manual review quality.
* Risk rules are configurable.

---

## Phase 8: Mobile and Field Verification

Purpose:

Support mobile-first and field-based verification workflows.

Core features:

* Flutter mobile app
* Offline draft capture
* Camera-guided document capture
* Camera-guided selfie capture
* Officer login
* Device registration
* Mobile audit logs
* Secure sync

Success criteria:

* Field officers can perform verification from mobile devices.
* Mobile sessions remain secure.
* Offline capture does not bypass consent or audit requirements.
* Device access can be revoked.

---

## Phase 9: Enterprise and Government Readiness

Purpose:

Prepare IdentityCore for larger regulated deployments.

Core features:

* Dedicated tenant deployments
* Private cloud support
* On-premise deployment option
* SIEM integration
* Advanced audit exports
* Advanced RBAC/ABAC
* SSO integration
* Data residency controls
* HSM support
* Enterprise reporting

Success criteria:

* Large institutions can deploy IdentityCore under stricter controls.
* Government pilots can be discussed with a working platform.
* Platform supports strong data isolation and audit requirements.

---

## Phase 10: Digital Trust Platform

Purpose:

Expand beyond identity verification into broader digital trust infrastructure.

Potential features:

* Digital credentials
* Verified profiles
* Secure access control
* Reusable verification tokens
* Organization trust scores
* Digital signatures
* Identity wallet integration
* Consent dashboard
* Trusted API marketplace

Success criteria:

* IdentityCore becomes more than verification.
* Organizations can build trusted services on top of the platform.
* Verification evidence can support future digital identity workflows.

---

## Long-Term Vision

IdentityCore may eventually support:

* Government identity integrations
* Passport authority integrations
* Transport authority integrations
* Healthcare identity verification
* Education identity verification
* Secure citizen service access
* Multi-biometric verification
* Authorized face search
* Disaster victim identification
* Missing persons workflows
* National digital trust infrastructure

These are long-term possibilities, not Version 1.0 commitments.

---

## Explicitly Out of Scope for Version 1.0

Version 1.0 will not include:

* Government database integrations
* Criminal records
* Immigration intelligence
* Mass surveillance
* Fingerprint recognition
* Iris recognition
* Digital identity wallet
* National identity issuance
* Centralized citizen database
* Law enforcement watchlists
* Fully autonomous high-impact decisions
* Offline verification
* Mobile app
* Payment processing

---

## Release Milestones

## 0.1 Internal Prototype

Includes:

* Basic Django backend
* Basic tenant model
* Basic verification creation
* Basic verification session
* Basic audit events

---

## 0.2 AI Prototype

Includes:

* FastAPI AI service
* Face detection
* Face matching
* Basic document quality check
* Basic OCR

---

## 0.3 End-to-End MVP

Includes:

* Consent
* Document upload
* Selfie capture
* Liveness
* Face match
* Decision engine
* Webhook result

---

## 0.4 Dashboard MVP

Includes:

* Organization dashboard
* Manual review
* API client management
* Webhook management
* Audit views

---

## 0.5 Pilot Release

Includes:

* Production deployment
* Monitoring
* Backups
* MFA
* Signed webhooks
* Rate limiting
* Pilot onboarding

---

## 1.0 Production MVP

Includes:

* Stable REST API
* Stable verification workflow
* Tenant isolation
* Audit logs
* Security controls
* Documentation
* Pilot-ready operations

---

## Roadmap Discipline

A feature may be added to the active roadmap only if it satisfies at least one of the following:

* Improves identity verification accuracy.
* Improves security.
* Improves privacy.
* Improves auditability.
* Improves organization integration.
* Improves Verification Subject experience.
* Reduces operational risk.

Features that do not support these goals should be postponed.

---

## Final Roadmap Principle

IdentityCore should grow through disciplined phases.

The goal is not to build every possible identity feature immediately. The goal is to build a trusted foundation that can safely expand into larger identity, trust, and government-grade workflows over time.
