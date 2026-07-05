# Testing Strategy

## IdentityCore

**Version:** 1.0

---

# Purpose

This document defines the testing strategy for IdentityCore.

The goal is to ensure that IdentityCore is secure, reliable, tenant-safe, privacy-preserving, and production-ready before handling real identity data.

---

# Testing Principle

IdentityCore must not treat testing as optional.

Because the platform handles identity documents, biometric data, API credentials, audit logs, and verification decisions, every critical workflow must be tested before release.

---

# Testing Pyramid

IdentityCore will use a layered testing approach:

```text
Unit Tests
    ↓
Integration Tests
    ↓
API Tests
    ↓
End-to-End Tests
    ↓
Security Tests
    ↓
Performance Tests
```

Most tests should be unit and integration tests.

End-to-end tests should cover only critical user journeys.

---

# Test Categories

## Unit Tests

Unit tests verify small pieces of logic in isolation.

Examples:

- Public ID generation
- Verification status transitions
- Permission checks
- Policy threshold logic
- Webhook signature generation
- Risk score calculation
- Consent validation

Rules:

- Must be fast.
- Must not depend on external services.
- Must run on every commit.

---

## Integration Tests

Integration tests verify that modules work together.

Examples:

- Creating a Verification creates a Verification Session.
- Accepting consent updates the Verification status.
- Uploading a document creates Document Capture records.
- Face match result updates Verification evidence.
- Verification Decision is created after required checks complete.
- Audit Event is created after sensitive action.

---

## API Tests

API tests verify REST and GraphQL behavior.

REST API tests should cover:

- Authentication
- Authorization
- Validation
- Pagination
- Filtering
- Idempotency
- Rate limiting
- Error format
- Tenant isolation

GraphQL tests should cover:

- Permission checks
- Query depth limits
- Field-level authorization
- Tenant filtering
- Sensitive field exposure

---

## End-to-End Tests

End-to-end tests verify complete workflows.

Critical E2E flows:

```text
Organization creates Verification
        ↓
Verification Subject opens link
        ↓
Consent accepted
        ↓
Document uploaded
        ↓
Selfie uploaded
        ↓
Liveness completed
        ↓
Face match completed
        ↓
Decision produced
        ↓
Webhook delivered
```

Other E2E flows:

- Verification expires.
- Verification is cancelled.
- Verification goes to Manual Review.
- Verification Officer records manual decision.
- Organization receives webhook result.

---

# Security Tests

Security tests are mandatory.

Required tests:

- Tenant isolation
- Permission enforcement
- API client scope enforcement
- API key authentication
- API client secret hashing
- API client tenant scoping
- Session token expiry
- Upload validation
- Webhook signature verification
- Sensitive data masking
- Object storage privacy
- GraphQL access control
- Rate limiting

---

# Tenant Isolation Testing

Tenant isolation is one of the highest-risk areas.

Every tenant-owned model must be tested to ensure one tenant cannot access another tenant's data.

Example:

```text
Tenant A creates Verification.
Tenant B attempts to access it.
Expected result: 404 or permission denied.
```

This must be tested for:

- Verifications
- Verification Subjects
- Identity Documents
- Document Captures
- Selfie Captures
- Audit Events
- API Clients
- Webhooks
- Policies
- Manual Reviews

---

# Permission Testing

Tests must verify that users only perform actions allowed by their roles.

Examples:

- Verification Officer cannot manage API Clients.
- Organization Administrator cannot view platform-wide audit logs.
- API Client without `verifications:read` cannot read Verification results.
- Platform User without manual review permission cannot approve cases.

---

# Authentication Testing

Authentication tests should cover:

- Valid login
- Invalid login
- Locked account
- Suspended account
- Inactive account
- JWT refresh
- Authenticated `/auth/me`
- MFA required
- Password reset
- Session expiry
- Session revocation
- API key authentication
- Invalid API secret
- Revoked API key

---

# Verification Workflow Testing

Verification workflow tests should cover:

- Verification creation
- Verification creation creates a Verification Subject and Verification Session
- Verification session retrieval validates the session token and returns portal context
- Expired verification sessions are rejected and marked expired
- Verification list endpoints remain tenant-scoped
- Verification detail requires `verifications:read`
- Verification cancellation updates status and timestamp
- Consent acceptance
- Document submission requires prior consent
- Document submission creates an Identity Document and Document Captures
- Document submission
- Selfie submission requires prior document submission
- Selfie submission creates a Selfie Capture and advances the next step
- Selfie submission
- Liveness submission requires a selfie capture from the same verification
- Liveness submission creates a Liveness Check placeholder and returns processing
- Liveness result processing
- Session status reflects subject-facing current step and message
- Liveness submission creates a Face Match placeholder tied to the verification evidence
- Verification detail responses reflect the latest liveness and face-match records
- Policy creation is tenant-scoped and versioned by policy name
- Verification creation copies a policy snapshot when `policy_id` is supplied
- Manual review listing is tenant-scoped
- Manual review decisions create a persisted verification decision and update verification status
- Liveness submission creates provider-check records for liveness and face match
- Liveness submission creates a persisted risk assessment and automatic decision
- Inconclusive bootstrap evidence routes verifications to manual review automatically
- Face match result processing
- Risk assessment
- Automatic approval
- Automatic rejection
- Manual review
- Expiration
- Cancellation
- Failure states

---

# AI Service Testing

The FastAPI AI service must be tested separately.

Tests should cover:

- Face detection with valid image
- Face detection with no face
- Face detection with multiple faces
- Face matching with same person
- Face matching with different people
- Liveness passed
- Liveness failed
- OCR success
- OCR low-confidence result
- Document quality pass
- Document quality fail
- Unsupported file format
- Large file rejection
- Model version returned

AI tests must use approved test data only.

Do not use real personal data without explicit consent.

---

# Mocking AI and Providers

During backend tests, external providers and AI services should be mocked.

The Django backend should not require real AI inference for normal test runs.

Test doubles should simulate:

- Successful OCR
- Failed OCR
- Passed liveness
- Failed liveness
- Matched face
- Unmatched face
- Provider timeout
- Provider error
- Inconclusive result

---

# File Upload Testing

File upload tests should cover:

- Valid image upload
- Invalid MIME type
- Oversized file
- Empty file
- Corrupt file
- Unsupported extension
- Duplicate upload
- Expired upload URL
- Upload without consent
- Upload for expired session

---

# Webhook Testing

Webhook tests should cover:

- Webhook event creation
- Signature generation
- Delivery success
- Delivery failure
- Retry behavior
- Exponential backoff
- Max retry limit
- Disabled webhook endpoint
- Duplicate delivery handling
- Idempotency on receiver side documentation

Current implemented webhook coverage includes:

- Webhook endpoint creation
- Tenant-scoped webhook endpoint listing
- Test webhook queueing
- Verification-created webhook queueing
- Manual decision webhook queueing
- Signature generation
- Delivery success handling
- Delivery failure retry scheduling
- Max retry failure handling
- Disabled endpoint cancellation
- Duplicate delivery short-circuiting
- Due-event processing only

Current implemented provider/risk coverage includes:

- Provider check validation enforces compatible provider/check-type combinations
- Completed provider checks require completion timestamps
- Rule-based risk evaluation supports automatic approval, rejection, and manual-review routing
- Verification detail responses include persisted risk-assessment summaries when present

Current implemented notification coverage includes:

- Verification-created notifications are queued when the subject email is present
- Verification cancellation queues a subject-facing notification
- Manual-review-required transitions queue subject and reviewer notifications
- Manual review decisions queue subject-facing status notifications
- Pending email notifications are delivered through the configured mail backend and marked sent
- Celery configuration routes webhook and notification delivery tasks to dedicated queues
- Celery beat configuration schedules periodic processing for pending webhooks and notifications

---

# Audit Testing

Audit tests should verify that sensitive actions create Audit Events.

Required audit coverage:

- Login
- Verification created
- Consent accepted
- Document uploaded
- Selfie uploaded
- Liveness completed
- Face match completed
- Manual decision recorded
- API Client created
- Webhook endpoint created
- Role changed
- Policy changed

Audit logs should not contain sensitive raw data.

Current implemented audit coverage includes:

- Login
- Verification created
- Consent accepted
- Document uploaded
- Selfie uploaded
- Liveness completed
- Face match completed
- Manual decision recorded
- API Client created

---

# Data Retention Testing

Retention tests should cover:

- Raw document deletion after retention period
- Selfie deletion after retention period
- Liveness media deletion
- Temporary upload cleanup
- Expired session cleanup
- Audit metadata preservation
- Deletion audit events

---

# Idempotency Testing

Critical POST endpoints must support idempotency.

Tests should verify:

- Same key and same payload returns same result.
- Same key and different payload returns error.
- Missing key works only where allowed.
- Idempotency records expire after configured period.

Required endpoints:

- Create Verification
- Create API Client
- Create Webhook Endpoint
- Manual Review Decision

---

# Error Handling Testing

Tests should verify that errors are safe and consistent.

Expected error behavior:

- No stack traces in API responses.
- No internal database IDs exposed.
- No secrets exposed.
- Standard error format used.
- Correct HTTP status codes returned.
- Request ID returned.

---

# Performance Testing

Initial performance tests should measure:

- Verification creation latency
- Verification result lookup latency
- Upload URL generation latency
- Webhook delivery latency
- AI processing latency
- Celery queue processing time
- Database query performance

Initial targets:

```text
Verification creation: < 500 ms
Verification lookup: < 300 ms
Face match processing: < 3 seconds
Liveness processing: < 5 seconds
OCR processing: < 5 seconds
Webhook delivery queueing: < 500 ms
```

---

# Load Testing

Load testing should simulate:

- Many verification creations
- Many Verification Subjects completing sessions
- Many file uploads
- AI queue backlog
- Webhook delivery bursts
- Dashboard list queries

Load testing is required before production pilots.

---

# Regression Testing

Every fixed bug should include a regression test.

Rule:

```text
If a bug reaches staging or production, write a test that would have caught it.
```

---

# Test Data

Test data must not contain real personal or biometric data unless explicitly approved.

Preferred test data:

- Synthetic identities
- Fake document images
- Public test images where licensing allows
- Generated files
- Mocked AI outputs

Sensitive test data must not be committed to Git.

---

# Test Environments

Testing environments:

```text
local
ci
staging
production-smoke
```

Production tests must be limited to safe smoke tests.

Never run destructive tests in production.

---

# Continuous Integration

CI should run on every pull request.

Required CI checks:

- Linting
- Formatting
- Type checks
- Unit tests
- Integration tests
- Security scans
- Dependency scans

Recommended tools:

```text
pytest
pytest-django
ruff
black
mypy
bandit
pip-audit
npm test
eslint
playwright
```

---

# Frontend Testing

Frontend tests should cover:

- Login screens
- Verification flow
- Consent screen
- Document upload UI
- Selfie capture UI
- Error states
- Manual review screen
- Dashboard tables
- API Client management
- Webhook management

Recommended tools:

```text
Vitest
React Testing Library
Playwright
```

---

# Manual Testing

Some areas require human testing.

Manual testing should cover:

- Camera behavior on real devices
- Document capture usability
- Selfie capture usability
- Liveness challenge experience
- Manual review usability
- Error messages
- Accessibility basics

---

# Accessibility Testing

Verification flows should be accessible.

Tests should check:

- Keyboard navigation
- Screen reader labels
- Color contrast
- Clear error messages
- Mobile responsiveness
- Alternative flows where possible

---

# Release Testing

Before every production release:

- All CI tests pass.
- Staging deployment succeeds.
- Database migrations are tested.
- Smoke tests pass.
- Critical E2E tests pass.
- Security-sensitive changes reviewed.
- Rollback plan exists.

---

# Production Smoke Tests

Safe production smoke tests may include:

- Health endpoint check
- Login page availability
- API authentication failure check
- Dashboard availability
- Worker heartbeat
- Database connectivity
- Redis connectivity
- Object storage connectivity

Do not create real Verification Subjects in production smoke tests unless using a dedicated test tenant.

---

# Minimum Coverage Targets

Initial targets:

```text
Core domain logic: 90%+
API views: 80%+
Security-sensitive modules: 90%+
AI service: 70%+
Frontend: critical flows only
```

Coverage is useful, but correctness matters more than chasing numbers.

---

# Test Ownership

Every module owner is responsible for tests covering that module.

For solo development, every new feature should include tests before being considered complete.

---

# Definition of Done

A feature is complete only when:

- It works as intended.
- It is tenant-safe.
- It enforces permissions.
- It has tests.
- It creates required audit events.
- It handles errors safely.
- It does not expose sensitive data.
- Documentation is updated where necessary.

---

# Version 1.0 Testing Scope

Version 1.0 testing includes:

- Unit tests
- Integration tests
- API tests
- Critical E2E tests
- Security tests
- Tenant isolation tests
- AI service tests
- Webhook tests
- Audit tests
- Upload tests
- Basic performance tests

Version 1.0 excludes:

- Full biometric certification testing
- Formal penetration testing certification
- Full accessibility certification
- Large-scale national load testing
- Multi-region failover testing

---

# Final Testing Principle

IdentityCore must be tested like a trust platform, not like an ordinary web app.

Every test should increase confidence that the system protects data, respects permissions, preserves auditability, and produces reliable verification outcomes.
