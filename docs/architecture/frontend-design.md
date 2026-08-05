# Frontend Design

## IdentityCore

**Version:** 2.0

---

### Purpose

This document defines the frontend architecture, user experience strategy, and application boundaries for IdentityCore.

IdentityCore is a **vendor-neutral identity infrastructure platform**.

Identity verification is the first workload implemented on the platform—not the boundary of the platform.

The frontend should expose IdentityCore in layers.

New customers should be able to complete identity verification without understanding providers, OCR, workflows, policies, evidence, claims, or the Provider Runtime.

Advanced customers should progressively discover and configure these capabilities as their requirements grow.

This follows the same philosophy used by cloud platforms such as AWS:

- Simple managed experiences first.
- Infrastructure capabilities available when needed.
- Progressive disclosure instead of exposing platform complexity immediately.

---

### Frontend Philosophy

The frontend should make sophisticated identity infrastructure feel simple.

Different users should see different parts of the platform.

A verification subject should never feel like they are interacting with infrastructure.

An organization administrator should configure workflows without understanding implementation details.

A developer should integrate with a clean API without needing to understand internal orchestration.

A platform administrator should have complete operational visibility.

The platform should reveal complexity only when it provides value.

---

### Frontend Applications

```text
frontend/

├── identitycore/
├── dashboard/
├── verification-portal/
├── developer-portal/
└── platform-admin/
```

Each application is responsible for a specific audience while sharing the same backend platform.

---

### Platform Architecture

```text
Applications

├── Public Website
├── Organization Dashboard
├── Verification Portal
├── Developer Portal
└── Platform Admin

                │
                ▼

        IdentityCore Platform

        Control Plane
        Execution Plane
        Provider Runtime
        Workflow Engine
        Policy Engine
        Evidence
        Claims
        Audit

                │
                ▼

Providers

- IdentityCore Managed Providers
- Commercial Providers
- Government Registries
- Customer-hosted Providers
- Storage Providers
- Risk Providers
- KMS/HSM Providers
```

None of the frontend applications communicate directly with providers.

All interaction occurs through IdentityCore APIs.

---

### Frontend Principles

Every frontend should:

- Hide unnecessary complexity
- Feel trustworthy
- Be fast
- Be accessible
- Be mobile-friendly
- Be privacy-aware
- Be security-conscious
- Be consistent across products

Users should not need to understand:

- OCR
- Face Matching
- Liveness
- Provider Routing
- Claims
- Evidence Lineage
- AI Models

unless they intentionally enter advanced configuration areas.

---

# Application Overview

## 1. Public Website

Application:

```text
frontend/identitycore
```

Audience:

- Prospective customers
- Developers
- Partners
- Procurement teams
- Compliance teams

Purpose:

The public website explains IdentityCore and acts as the entry point into the platform.

Primary features:

- Product overview
- Platform overview
- Workloads
- Pricing
- Documentation entry
- Security
- Compliance
- Company
- Contact
- Blog
- Status

The public website should clearly communicate:

> IdentityCore is identity infrastructure.

not simply:

> Identity verification software.

---

### 2. Organization Dashboard

Application:

```text
frontend/dashboard
```

Audience:

- Organization Administrators
- Developers
- Compliance Officers
- Operations Teams
- Verification Teams

Purpose:

The dashboard is the organization's **Control Plane**.

Identity verification is currently the primary workload available through the dashboard.

Future workloads should appear naturally without redesigning the application.

---

## Dashboard Areas

### Overview

- Usage
- Activity
- Notifications
- Health

---

### Workloads

Current:

- Identity Verification

Future:

- Age Verification
- Organization Verification
- Identity Resolution
- Verified Claims
- Credential Verification

Selecting a workload changes the operational views while preserving the same platform concepts.

---

### Workflows

Organizations should be able to:

- View workflows
- Version workflows
- Activate workflows
- Test workflows

Version 1 focuses primarily on verification workflows.

---

### Policies

Organizations should configure:

- Verification Policies
- Risk Policies
- Manual Review Policies
- Retention Policies
- Privacy Policies

Policies should remain understandable without exposing implementation complexity.

---

### Providers

Organizations should manage:

- Managed Providers
- Customer-hosted Providers
- Commercial Providers
- Provider Assignments
- Capability Routing
- Health
- Credentials
- Test Connections

Most organizations should never need to modify these.

Defaults should work well.

---

### Evidence

Organizations should view:

- Verification Evidence
- Document Evidence
- Biometric Evidence
- Audit Trail
- Evidence Timeline

Evidence should be human-readable.

---

### Manual Review

Reviewers should:

- Review evidence
- Approve
- Reject
- Request additional evidence
- Escalate
- Record notes

Maker-checker approval should appear when required.

---

### Developers

Developers should manage:

- API Keys
- SDK Credentials
- Webhooks
- API Logs
- Usage
- Environments

---

### Organization

- Projects
- Environments
- Team
- Roles
- Audit
- Billing
- Settings

---

### 3. Verification Portal

Application:

```text
frontend/verification-portal
```

Audience:

Verification Subjects.

Purpose:

The Verification Portal is a workload-specific frontend for the identity verification workload.

The subject should never feel like they are using enterprise software.

Typical flow:

1. Customer onboarding
2. Organization Information
3. Verification Purpose
4. Consent
5. Document Capture
6. Selfie Capture
7. Liveness
8. Submission
9. Status

The interface should:

- explain what is required;
- explain why it is required;
- explain how the information will be used;
- minimize cognitive load.

The portal should remain mobile-first.

---

### 4. Developer Portal

Application:

```text
frontend/developer-portal
```

Audience:

Developers.

Purpose:

The Developer Portal is the primary developer experience for IdentityCore.

It should feel similar to:

- Stripe
- Supabase
- Twilio
- Vercel

Features:

- API Reference
- SDK Downloads
- CLI
- Quick Start
- Authentication
- Workflows
- Policies
- Verification Examples
- Provider SDK
- Webhooks
- Sandbox
- Changelog
- Release Notes
- Capability Reference
- Error Reference

Developers should understand:

> Applications integrate with IdentityCore.

not

> Applications integrate with OCR.

---

### 5. Platform Admin

Application:

```text
frontend/platform-admin
```

Audience:

IdentityCore Operations.

Purpose:

The Platform Admin application manages the platform itself.

Features:

- Organizations
- Projects
- Platform Users
- Managed Providers
- Provider Registry
- Provider Health
- Provider Runtime
- Capability Registry
- Workflow Templates
- Policy Templates
- Platform Monitoring
- Audit
- Privacy Operations
- Subject Exports
- Deletion Requests
- Billing
- Feature Flags
- API Versions
- SDK Versions
- Incident Management

This application is intentionally separate from customer dashboards.

---

### API Strategy

The frontend communicates only with IdentityCore.

IdentityCore communicates with providers.

---

## Organization Dashboard

GraphQL should be used for:

- connected data
- dashboards
- administration
- reporting
- policy management

---

## Verification Portal

REST should be used where appropriate for:

- session retrieval
- uploads
- consent
- submission
- status

The portal is intentionally optimized for SDK compatibility and public session flows.

---

## Developer Portal

Primarily static documentation with authenticated developer tooling where appropriate.

---

## Platform Admin

GraphQL for operational management.

---

### Design System

IdentityCore should have one design system shared by every frontend.

Technology:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

The design system should prioritize:

- consistency
- accessibility
- composability
- responsiveness
- performance

---

### Theme Strategy

Supported themes:

- System
- Light
- Dark

Default:

System

Fallback:

Light

---

### Visual Direction

IdentityCore should look:

- Professional
- Modern
- Calm
- Trustworthy

Avoid:

- excessive animations
- playful enterprise UI
- clutter
- visual noise

Use:

- generous whitespace
- clear typography
- obvious status indicators
- accessible colors
- meaningful empty states

---

### No-Code Experience

IdentityCore should support organizations without engineering teams.

Organizations should be able to:

- Create verification requests
- Generate secure links
- Send links
- Review results
- Configure policies
- Export reports

Future workloads should reuse the same experience.

---

### Workflow & Policy Builder

Version 1 emphasizes policy-driven verification.

Future versions may expose richer workflow composition.

Organizations should eventually configure:

- workflow steps
- provider selection
- retries
- fallback
- Manual Review
- notifications
- retention
- webhooks

without writing code.

---

### Accessibility

Every frontend should support:

- keyboard navigation
- screen readers
- clear labels
- high contrast
- responsive layouts
- meaningful validation
- informative error states

Accessibility is a platform requirement rather than an optional enhancement.

---

### Security Requirements

Frontend applications must:

- never expose API secrets;
- never expose provider credentials;
- use secure session handling;
- respect tenant and environment isolation;
- minimize displayed personal information;
- mask sensitive fields where appropriate;
- avoid exposing internal implementation details.

---

### Version 2 Platform Scope

Current primary workload:

- Identity verification

Current applications:

- Public Website
- Organization Dashboard
- Verification Portal
- Developer Portal
- Platform Admin

Current platform capabilities include:

- workflow execution
- policy management
- provider runtime
- evidence
- manual review
- audit
- APIs
- SDKs

Future platform capabilities may include:

- verified claims
- credential verification
- age verification
- organization verification
- identity resolution
- additional trust workloads

---

### Final Principle

IdentityCore should make identity infrastructure feel effortless.

A first-time customer should experience a simple identity verification workflow.

An advanced organization should discover a powerful identity infrastructure platform without needing to migrate to a different product.

Complexity belongs inside the platform—not in front of the user.
