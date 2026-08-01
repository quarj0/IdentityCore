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

This means the application is **feature-complete for its current engineering scope**:
public acquisition, organization account entry, onboarding, verification-portal handoff,
and first-workflow creation. Production release approval still depends on the external
certification and operational items called out below.

## Status at a glance

This table is the source of truth for interpreting the sections below. “Implemented”
means the code path exists; it does not mean the path has completed production browser,
security, accessibility, and operational certification.

| Capability                                                                   | Status                               | What remains                                                                                                                              |
| ---------------------------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Public pages and responsive design foundation                                | Implemented                          | Final content/legal approval, localization, analytics/privacy decisions, and visual regression.                                           |
| Registration and organization workspace creation                             | Implemented                          | Browser tests, duplicate/partial-registration recovery, accepted legal-version records, and abuse controls.                               |
| Email verification and password recovery                                     | Implemented                          | Delivery state, resend cooldowns, expired-link recovery tests, and support references.                                                    |
| Login, refresh-cookie rotation, password change, and session-expiry recovery | Implemented                          | MFA is a separate account-security feature when enabled by backend policy.                                                                |
| Server-backed logout                                                         | Implemented                          | Automated desktop/mobile tests and operational monitoring.                                                                                |
| Organization profile and evidence submission                                 | Implemented                          | Unified upload contract, checksums, interruption/cancellation behavior, and end-to-end tests.                                             |
| Administrator verification launch                                            | Implemented                          | Cross-application completion contract and failure/expiry browser tests.                                                                   |
| Camera, active liveness, and mobile handoff                                  | Implemented in `verification-portal` | Device/browser, security, accessibility, and provider-backed production certification; do not rebuild it here.                            |
| Published workflow-template catalog                                          | Implemented                          | Seed/author approved production templates and add contract/E2E coverage.                                                                  |
| Idempotent first-workflow creation                                           | Implemented                          | End-to-end onboarding test and authoritative onboarding completion action.                                                                |
| Backend template-instantiation tests                                         | Implemented                          | Keep them in the backend CI suite.                                                                                                        |
| Authoritative onboarding navigation                                          | Implemented                          | The server-authored `currentStep` limits future-step access; richer allowed-action/blocker payloads remain an API enhancement.            |
| SEO, discovery metadata, and indexing controls                               | Implemented                          | Supply approved production origin/indexing environment values and monitor indexing after release.                                         |
| Generated REST/GraphQL clients                                               | Deferred hardening                   | Generate types from schemas and enforce drift checks in CI before broad external API evolution.                                           |
| IdentityCore-web automated tests                                             | Started                              | Safe return-route unit tests exist; add component, Playwright, accessibility, and visual suites when browser infrastructure is available. |
| Production release certification                                             | Not complete                         | Security headers/deployment validation, observability, legal approval, browser matrix, runbooks, and release promotion.                   |

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
- **Transactional first workflow: implemented.** The backend now exposes a published,
  versioned template catalog and an idempotent project-scoped instantiation transaction.
  The onboarding page selects a real template, previews its steps, providers, and claims,
  creates a lineage-linked sandbox workflow, and uses the returned workflow ID for the
  dashboard handoff.

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

### 3. Make “choose first workflow” a transaction — implemented

Published workflow templates now carry executable steps, settings, provider requirements,
and output claims. Instantiation copies the selected version into the tenant project,
records immutable lineage and an audit event, and safely replays an idempotency key. The
onboarding UI uses the returned workflow rather than inferring selection from a list.

Implemented API shape:

```text
GET  /api/v1/workflow-templates
GET  /api/v1/workflow-templates/{template_id}
POST /api/v1/projects/{project_id}/workflows:instantiate
```

The create call should accept a template version and idempotency key and return the
created workflow public ID.

### 4. Close onboarding state transitions — implemented for the current workflow

Onboarding pages now use the backend `currentStep` projection and prevent navigation into
future steps. Organization submission/resubmission, administrator launch/resume/retry,
automatic platform review, first-workflow creation, review notes, and dashboard entry use
real backend operations. A future generalized workflow engine may add explicit
`allowed_actions` and `blockers`; that is not required to complete this fixed onboarding
journey.

### 5. Finish authentication and account security

Server-backed logout revokes the refresh token, clears its cookie, and always removes the
browser session on desktop and mobile. Refresh failure now emits an expiry event, safely
returns the user to login, and restores only validated internal routes after sign-in.
MFA enrollment/challenge/recovery remains a separate feature when backend policy enables
MFA; it is not part of the current organization-onboarding completion boundary.

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

### 8. Add onboarding projection and action endpoints — current projection implemented

The current GraphQL onboarding object supplies the canonical current step and mutation
next actions used by the frontend guard and forms. If onboarding becomes dynamically
configurable, extend it with the following generalized fields rather than recreating
policy in the client:

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

### 11. Complete public-site discovery and SEO — implemented

The app now has infrastructure-focused metadata, a configurable canonical origin,
OpenGraph/Twitter imagery, a public-route sitemap, a web manifest, and environment-aware
indexing controls. Individual campaign pages may add richer structured data as marketing
requirements evolve.

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

The engineering scope is complete. Remaining release/certification work is:

1. Run the complete browser/accessibility/visual suite once CI browser infrastructure is available.
2. Approve final legal and product claims and decide whether optional analytics will be enabled.
3. Certify the organization-evidence upload and verification-portal handoff under interruption and expiry.
4. Configure production origins, CSP dependencies, indexing, monitoring, and release rollback.
5. Complete the security/privacy review and supported-browser sign-off.

Do not reopen completed features in this application when work moves to
`frontend/verification-portal`; record integration defects against the owning application
and keep the capture implementation single-sourced.
