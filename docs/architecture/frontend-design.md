# Frontend Design

## IdentityCore

**Version:** 1.0

---

## Purpose

This document defines the frontend structure, user experience, and interface strategy for IdentityCore.

IdentityCore has multiple user-facing applications, each serving a different audience.

---

## Frontend Applications

IdentityCore will use separate frontend applications:

```text
frontend/

├── identitycore/
├── dashboard/
├── verification-portal/
├── developer-portal/
└── platform-admin/
```

### Public Website

`frontend/identitycore` is the public website and landing experience for IdentityCore.

Main features:

- Product landing pages
- Pricing and packaging pages
- Trust, security, and compliance pages
- Company and contact pages
- Public onboarding entry points
- Navigation into dashboard, verification, and developer experiences

This frontend is separate from the product applications so marketing, trust messaging, and public discovery do not compete with authenticated workflows.

---

## 1. Organization Dashboard

The Organization Dashboard is used by customer organizations.

Primary users:

- Organization Administrator
- Verification Officer
- Developer
- Compliance Reviewer

Main features:

- Organization onboarding
- Organization profile
- Projects
- Verification policies
- Verification requests
- Verification subjects
- Manual review
- API keys
- Webhooks
- Audit logs
- Reports
- Team management
- Billing
- Settings

---

## 2. Verification Portal

The Verification Portal is used by the Verification Subject.

This is the page opened from a verification link.

Main steps:

1. View organization requesting verification
2. Review verification purpose
3. Accept consent
4. Upload identity document
5. Capture selfie
6. Complete liveness check
7. Submit verification
8. View completion status

The Verification Portal should be simple, mobile-first, and distraction-free.

The Verification Subject should not see dashboard functionality.

---

## 3. Developer Portal

The Developer Portal is for technical customers.

Main features:

- API documentation
- Quick start guides
- SDK examples
- API key instructions
- Webhook documentation
- Testing tools
- Sandbox information
- Error code reference

The Developer Portal should feel similar to Stripe, Twilio, or Supabase documentation.

---

## 4. Platform Admin Portal

The Platform Admin Portal is used internally by IdentityCore administrators.

Main features:

- Review organization onboarding
- Approve or reject organizations
- Manage organization tiers
- View all tenants
- Monitor verification activity
- Review abuse signals
- Manage providers
- View platform audit logs
- Manage system settings

This portal is separate from customer dashboards.

---

## Frontend Technology

IdentityCore frontends will use:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui or similar component system
- GraphQL for dashboard/admin data
- REST for public verification flow where appropriate

---

## API Usage

### Dashboard

The dashboard should use GraphQL.

Examples:

- Organization settings
- Verification statistics
- Policy builder
- Manual review
- API key management
- Webhook management
- Team management

### Verification Portal

The verification portal may use REST because the flow is simple, public, and session-token based.

Examples:

- Fetch session
- Accept consent
- Request upload URL
- Submit document
- Submit selfie
- Submit liveness result
- Check status

### Developer Portal

The developer portal may be mostly static content with selected authenticated dashboard features.

---

## Design Principles

IdentityCore UI should be:

- Professional
- Clean
- Fast
- Trustworthy
- Accessible
- Mobile-friendly
- Minimal
- Security-conscious

The interface should not feel like Django Admin.

It should feel closer to modern developer tools such as Stripe, Vercel, Linear, GitHub, and Supabase.

---

## Theme Strategy

IdentityCore should support both light mode and dark mode.

However, light mode should be the default for Version 1.0.

Reason:

- Identity verification is a trust-sensitive workflow.
- Many government, enterprise, and compliance users expect clear light interfaces.
- Uploaded documents and selfies are easier to inspect against a neutral light background.
- Light mode feels more formal for onboarding, compliance, and review tasks.

Dark mode should be available as a user preference, not forced.

Recommended modes:

```text
System default
Light
Dark
```

Default:

```text
System default
```

If system preference is unknown, use light mode.

---

## Visual Direction

The product should use:

- Neutral colors
- Clear spacing
- Strong typography
- Minimal animations
- Clear status badges
- High contrast buttons
- Simple cards
- Professional tables
- Clear error states

Avoid:

- Overly playful colors
- Heavy animations
- Crowded dashboards
- Complex gradients
- Low contrast text
- Dark-only design

## Suggested Domain Split

Recommended routing:

- `www.identitycore.com` or root domain -> `identitycore`
- `app.identitycore.com` -> `dashboard`
- `verify.identitycore.com` or `/verify` -> `verification-portal`
- `docs.identitycore.com` -> `developer-portal`
- `admin.identitycore.com` -> `platform-admin`

---

## Dashboard Layout

Recommended layout:

```text
Sidebar
Top bar
Main content area
Contextual actions
```

Sidebar sections:

```text
Overview

Verifications
- Requests
- Subjects
- Manual Review
- Policies

Developers
- API Keys
- Webhooks
- Logs

Organization
- Team
- Audit Logs
- Billing
- Settings
```

---

## Verification Portal UX

The Verification Portal should be step-based.

Example:

```text
Step 1: Consent
Step 2: Document
Step 3: Selfie
Step 4: Liveness
Step 5: Complete
```

Each step should clearly explain:

- What is needed
- Why it is needed
- How the data will be used
- What happens next

---

## No-Code Verification

The dashboard shall support no-code verification workflows.

Organization users should be able to:

- Create verification requests
- Generate secure verification links
- Copy links
- Send links by email later
- View results
- Manually review cases
- Export reports

This allows non-technical organizations to use IdentityCore without API integration.

---

## Verification Policy Builder

The dashboard shall provide a no-code policy builder.

Users should be able to configure:

- Accepted document types
- Required selfie
- Required liveness
- Face match threshold
- Manual review threshold
- Verification expiry
- Retention period
- Webhook events

The policy builder should write to the same backend Verification Policy system used by APIs.

---

## Accessibility

Frontend applications should support:

- Keyboard navigation
- Clear labels
- Good contrast
- Mobile responsiveness
- Helpful error messages
- Screen reader-friendly forms where practical

---

## Security Requirements

Frontend applications must:

- Never expose API secrets
- Never store sensitive tokens insecurely
- Never expose internal database IDs
- Use secure session handling
- Respect tenant boundaries
- Avoid showing unnecessary personal data
- Mask sensitive fields where appropriate

---

## Version 1.0 Scope

Version 1.0 frontend includes:

- Organization Dashboard
- Verification Portal
- Basic Developer Portal
- Platform Admin Portal foundation
- Light mode default
- Dark mode support
- No-code verification request creation
- Verification policy builder
- Manual review interface
- API key management
- Webhook management

Version 1.0 excludes:

- Advanced analytics dashboards
- White-label custom domains
- Full drag-and-drop workflow builder
- Mobile app
- Public marketplace
- Advanced compliance exports

---

## Final Frontend Principle

IdentityCore's frontend should make complex identity infrastructure feel simple, safe, and trustworthy.

The user should not need to understand OCR, face matching, liveness, or AI models.

They should understand one thing clearly:

IdentityCore helps their organization verify identity securely.
