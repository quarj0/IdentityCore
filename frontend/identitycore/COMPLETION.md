# IdentityCore Web Completion Plan

Last reviewed: 2026-07-26

## Scope

`frontend/identitycore` is the public IdentityCore website plus organization account
entry and onboarding application. It is not the authenticated operations dashboard or
the general applicant verification portal. Its completion boundary is:

1. explain IdentityCore accurately as identity infrastructure;
2. convert visitors into organization workspaces or qualified contact requests;
3. authenticate organization users safely;
4. complete email, organization, and administrator onboarding;
5. hand an approved organization into the dashboard without a broken transition.

## Current state

The application has a broad, buildable UI foundation:

- public landing, platform, solutions, templates, developer, security, pricing,
  company, contact, and legal pages;
- registration, login, email verification, password reset, and password change;
- organization profile and evidence submission, administrator identity verification,
  production approval status, and first-workflow handoff;
- live GraphQL calls for public catalog, registration, email verification, contact,
  password recovery, and onboarding state;
- live REST calls for authentication, organization evidence uploads, workflows, and the
  embedded administrator-verification session;
- shared request timeout, token refresh, API error handling, and production-origin
  validation;
- clean ESLint and production Next.js builds.

This means the frontend is not an empty mock. It is a functioning vertical slice, but it
is not complete or production-ready.

## P0: complete the real user journeys

### Implementation progress

- **Verification application boundary: implemented.** New administrator sessions already
  launch the dedicated verification portal. The legacy `/verification` entry point now
  performs a compatibility redirect to that portal, moving its query-string credential
  into a URL fragment. The duplicate document, selfie, passive-liveness, evidence, and
  verification API implementation has been removed from this application.
- **Live capture implementation: owned by `verification-portal`.** That application
  contains camera capture, server-issued active liveness challenges, short video capture,
  upload fallback, and mobile handoff. Remaining work here is cross-application contract,
  security, accessibility, and browser certification rather than another capture UI.

### 1. Separate organization onboarding from applicant verification

Administrator verification is now owned by `frontend/verification-portal`. Keep the
legacy compatibility redirect until previously issued links have expired, then remove
the route. Formalize the completion contract between onboarding and the verification
domain so this frontend reads authoritative state rather than receiving internal
evidence. Do not reintroduce document, selfie, or liveness capture here.

### 2. Replace upload-only biometrics with real capture UX

Complete end-to-end certification of the dedicated portal's camera capture, permissions,
framing/quality guidance, retry states, active challenges, mobile handoff, device
compatibility, and accessible fallbacks. IdentityCore web should only launch the portal
and reflect its server-authored completion state.

### 3. Make “choose first workflow” a transaction

Public workflow templates are static frontend data, and “Use this template” redirects to
the dashboard. The onboarding first-workflow page merely reads the first existing
workflow. Add a canonical backend template catalog and an idempotent API that instantiates
a selected, versioned template into the current tenant/project/environment. The UI must
show preview, provider requirements, policy defaults, creation progress, validation
errors, and the created workflow—not infer selection from `workflows[0]`.

Required API shape:

```text
GET  /api/v1/workflow-templates
GET  /api/v1/workflow-templates/{template_id}
POST /api/v1/projects/{project_id}/workflows:instantiate
```

The create call should accept a template version and idempotency key and return the
created workflow public ID.

### 4. Close onboarding state transitions

Make every page enforce backend-authorized progression instead of only rendering links.
Add explicit actions for organization resubmission, administrator resume/retry, first
workflow completion, production application submission, withdrawal, and dashboard entry.
Display review reason codes and next actions consistently. Prevent stale tabs from
performing invalid transitions and preserve unsaved form data where safe.

### 5. Finish authentication and account security

Add logout and session-expiry handling to the onboarding shell; verify refresh-cookie
rotation/reuse detection; redirect unauthenticated users consistently; restore the
intended route after login; handle disabled, invited, locked, and MFA-required accounts;
and provide MFA enrollment/challenge/recovery when enabled by backend policy. Avoid
keeping user profile data in persistent local storage unless it is necessary and safe.

## P0: API and contract work

### 6. Generate typed clients from contracts

The application hand-writes REST response interfaces and GraphQL selection sets. Add
OpenAPI and GraphQL code generation, check generated clients in CI, and fail when the
backend schema and frontend operations drift. Use one shared API client package rather
than app-specific request models wherever possible.

### 7. Standardize upload contracts

Organization evidence uses an initiate/content/complete sequence while session evidence
uses an upload/transfer sequence. Define one typed upload abstraction that supports both
same-origin transfer paths and absolute pre-signed object-storage URLs. Direct storage
uploads must not be sent through the JSON envelope parser, and completion should verify
size, MIME type, checksum, ownership, and upload state. Add cancellation and abandoned
upload cleanup behavior.

### 8. Add onboarding projection and action endpoints

The current GraphQL onboarding object is broad, but the frontend still derives important
business state locally. Return a server-authored list of allowed actions and canonical
next route so frontend logic cannot disagree with workflow policy.

Recommended fields:

```text
onboarding.status
onboarding.current_step
onboarding.allowed_actions[]
onboarding.blockers[]
onboarding.next_action
onboarding.updated_at
```

### 9. Add public content APIs or an explicit publishing workflow

Countries and document types are live, but solutions, templates, pricing, provider
examples, security claims, company content, and legal documents are source-controlled
frontend data. Decide deliberately between:

- keeping them versioned in code with review and release ownership; or
- serving versioned published content from a CMS/content API with preview and rollback.

Pricing, compliance, provider availability, and legal effective dates must not become
unreviewed marketing constants.

## P1: product completeness

### 10. Align every page with the infrastructure positioning

Audit titles, metadata, templates, solutions, diagrams, and CTAs so IdentityCore is
consistently presented as the identity control plane and provider ecosystem. Clearly
label built-in, available integration, preview, and roadmap capabilities. Do not imply
that BYOP, private cloud, on-premises deployment, provider routing, or credentials are
production-ready until the corresponding runtime exists.

### 11. Complete public-site discovery and SEO

Add a canonical production site URL, per-route metadata, canonical links, sitemap,
OpenGraph/Twitter images, structured data, favicons/manifest, and environment-aware
robots behavior. The current root metadata remains verification-heavy and there is no
sitemap or social image asset.

### 12. Complete accessibility and responsive QA

Test keyboard-only navigation, focus restoration, flyouts/dialogs, screen-reader status
announcements, form-error association, progress semantics, contrast, reduced motion,
zoom, RTL readiness, and mobile layouts. Fix structural markup issues such as redundant
registration header wrappers and ensure loading states expose accessible text.

### 13. Complete legal, consent, and privacy behavior

Replace draft legal copy with approved, versioned notices and effective dates. Record
the privacy/terms versions accepted during registration. If non-essential analytics or
marketing cookies are enabled, implement a real consent manager and honor withdrawal.
Ensure verification consent is purpose-specific and comes from the verification policy,
not hard-coded administrator wording.

### 14. Add communications and recovery UX

Add email-delivery status and resend cooldowns, expired-link recovery, support references,
duplicate-registration handling, organization invitation acceptance, and clear recovery
from partial onboarding. Contact submissions should include abuse protection, consent,
rate-limit feedback, and an inquiry reference.

### 15. Add observability without leaking identity data

Instrument page and API failures, onboarding funnel transitions, web vitals, and release
version while redacting tokens, document identifiers, identity fields, and signed URLs.
Add a user-facing incident/support path and correlation/request IDs to error screens.

## P1: testing and release gates

There are currently no application-local unit, component, or browser tests. Add:

- unit tests for registration validation, onboarding routing, auth/session behavior,
  error normalization, template selection, and upload state machines;
- component tests for every form, error state, retry, disabled state, and accessible
  announcement;
- API contract tests for every GraphQL operation and REST call;
- Playwright journeys for register -> verify email -> login -> organization evidence ->
  administrator verification -> workflow selection -> production review;
- browser/device tests for camera, upload, mobile handoff, refresh expiry, deep links,
  slow networks, and interrupted uploads;
- automated accessibility scans and visual regression at supported breakpoints.

Required CI gates should include:

```text
pnpm --filter identitycore-web lint
pnpm --filter identitycore-web exec tsc --noEmit
pnpm --filter identitycore-web test
pnpm --filter identitycore-web test:e2e
pnpm --filter identitycore-web build
```

## P2: operational readiness

- define supported browsers/devices and camera requirements;
- add CSP, frame-ancestors, permissions policy, HSTS, and other deployment headers;
- verify CORS, CSRF, cookie, redirect, and trusted-origin settings in each environment;
- add dependency, secret, SAST, and bundle-size checks;
- establish preview, sandbox, staging, and production deployment promotion;
- add feature flags, rollback, synthetic journeys, uptime objectives, and runbooks;
- localize content, dates, phone numbers, document names, and accessibility strings;
- run threat modeling and privacy review for every route that handles organization or
  identity evidence.

## Suggested delivery order

1. Establish generated contracts and browser test infrastructure.
2. Unify the verification capture boundary with `verification-portal`.
3. Complete real camera/liveness and resilient uploads.
4. Implement transactional workflow-template selection.
5. Close authentication, onboarding actions, and production handoff.
6. Align content/claims and complete legal, accessibility, SEO, and observability.
7. Certify security, browsers, environments, and release operations.

The frontend is complete when these journeys work against real APIs under success,
failure, retry, expiry, and review outcomes—not merely when every route has a rendered
page.
