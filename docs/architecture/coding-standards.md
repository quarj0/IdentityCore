# Coding Standards

## IdentityCore

**Version:** 1.0

---

# Purpose

This document defines coding standards for IdentityCore.

The goal is to keep the codebase secure, readable, consistent, maintainable, and scalable as the platform grows.

---

# Core Principles

IdentityCore code must be:

- Secure by default
- Easy to understand
- Easy to test
- Explicit rather than clever
- Consistent across modules
- Tenant-aware
- Auditable where required

---

# Technology Stack

Version 1.0 uses:

```
Backend:
Django
Django REST Framework
Celery
PostgreSQL
Redis

AI Service:
FastAPI
Pydantic
OpenCV
ONNX Runtime
OCR libraries

Frontend:
Next.js
TypeScript
React
Tailwind CSS

Infrastructure:
Docker
Docker Compose
GitHub Actions
```

---

# Repository Structure

Recommended structure:

```
identitycore/

backend/
├── django/
└── fastapi-ai/

frontend/
├── dashboard/
├── verification-portal/
└── developer-portal/

infrastructure/
├── docker/
├── nginx/
└── scripts/

docs/
├── foundation/
├── architecture/
├── decisions/
├── research/
└── notes/
```

---

# Python Standards

Python code must follow:

- PEP 8
- Type hints where practical
- Clear function names
- Small functions
- Explicit exceptions
- No unused imports
- No hardcoded secrets

Recommended tools:

```
ruff
black
mypy
pytest
bandit
```

---

# Django Standards

Django apps should be domain-based.

Example:

```
apps/
├── accounts/
├── tenants/
├── organizations/
├── verifications/
├── documents/
├── biometrics/
├── consent/
├── audit/
└── webhooks/
```

Each app should follow:

```
models.py
serializers.py
views.py
services.py
selectors.py
permissions.py
tasks.py
tests/
```

---

# Service Layer Pattern

Business logic should not live directly in views.

Preferred flow:

```
View / API endpoint
        ↓
Serializer validation
        ↓
Service function
        ↓
Model/database operation
        ↓
Audit/event emission
```

Example:

```python
create_verification(
    tenant=tenant,
    subject_data=subject_data,
    policy=policy,
    purpose=purpose,
)
```

---

# Selectors Pattern

Read-heavy queries should live in selectors.

Example:

```python
get_verification_for_tenant(
    tenant=tenant,
    verification_public_id=verification_id,
)
```

This keeps query logic reusable and tenant-safe.

---

# Tenant Safety

Every tenant-owned query must include tenant context.

Bad:

```python
Verification.objects.get(public_id=verification_id)
```

Good:

```python
Verification.objects.get(
    tenant=request.tenant,
    public_id=verification_id,
)
```

Tenant filtering is mandatory.

---

# Public IDs

Do not expose internal database IDs.

Use prefixed ULID public IDs.

Examples:

```
org_01J...
ten_01J...
ver_01J...
sub_01J...
doc_01J...
aud_01J...
```

Internal IDs are for database relationships only.

---

# Naming Conventions

Use domain language consistently.

Use:

```
Verification Subject
Identity Document
Document Capture
Selfie Capture
Liveness Check
Face Match
Verification Decision
Audit Event
Provider Adapter
```

Avoid:

```
End User
User photo
Face scan
Ghana Card as a core term
Customer document
```

---

# API Standards

All REST responses must follow the standard format.

Success:

```json
{
  "success": true,
  "data": {},
  "request_id": "req_01J..."
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid request.",
    "details": {}
  },
  "request_id": "req_01J..."
}
```

---

# Error Handling

Errors should be explicit and safe.

Do not expose:

- Stack traces
- Secrets
- Internal provider responses
- Raw SQL errors
- File paths
- Internal IDs

Use domain-specific errors where possible.

---

# Logging Standards

Logs must be structured.

Include:

- request_id
- tenant_id
- actor_id
- action
- status
- duration

Never log:

- Passwords
- API secrets
- Session tokens
- Raw biometric templates
- Full document numbers
- Raw identity documents
- Selfie images

---

# Audit Events

Sensitive actions must create audit events.

Examples:

- User login
- Verification created
- Consent accepted
- Document uploaded
- Selfie uploaded
- Manual decision recorded
- API key created
- Role changed
- Webhook configured

Audit events should be emitted from the service layer.

---

# Celery Standards

Celery tasks must be:

- Idempotent where possible
- Tenant-aware
- Safe to retry
- Logged
- Timeout-protected

Tasks should receive public IDs or explicit tenant context, not random unscoped database IDs.

---

# FastAPI AI Service Standards

The AI service must:

- Use Pydantic schemas
- Validate all inputs
- Return model name and version
- Never make final verification decisions
- Avoid logging sensitive media
- Fail safely

AI endpoints return technical results, not business decisions.

---

# Frontend Standards

Frontend code must use:

- TypeScript
- Functional React components
- Clear component names
- Form validation
- API client abstraction
- Strict handling of sensitive data

Do not expose secrets in frontend code.

---

# Security Standards

All code must follow:

- Input validation
- Output escaping
- Permission checks
- Tenant checks
- Secure defaults
- Least privilege

Security-sensitive changes require careful review.

---

# Testing Standards

Every feature should include tests for:

- Expected success path
- Validation errors
- Permission failures
- Tenant isolation
- Edge cases

Security-sensitive modules require extra tests.

---

# Git Standards

Branch naming:

```
feature/verification-sessions
fix/webhook-retry
chore/docker-setup
docs/api-spec-update
security/api-key-rotation
```

Commit style:

```
feat: add verification session model
fix: enforce tenant filter on verification lookup
docs: update API specification
test: add webhook signature tests
security: mask API secrets in logs
```

---

# Pull Request Standards

Every pull request should include:

- What changed
- Why it changed
- How it was tested
- Screenshots where applicable
- Security considerations where applicable

---

# Dependency Standards

Dependencies must be:

- Necessary
- Maintained
- Compatible with the project license
- Scanned for vulnerabilities

Avoid adding packages for simple functionality.

---

# Environment Configuration

Use environment variables for configuration.

Do not hardcode:

- Secrets
- URLs
- Credentials
- API keys
- Environment-specific settings

---

# Documentation Standards

Update documentation when changing:

- APIs
- Database schema
- Architecture
- Security behavior
- Deployment behavior
- Domain concepts

Major decisions require an ADR.

---

# Code Review Checklist

Before merging code, check:

- Does it enforce tenant isolation?
- Does it require correct permissions?
- Does it avoid logging sensitive data?
- Does it use public IDs externally?
- Does it include tests?
- Does it follow domain language?
- Does it fail safely?
- Does it update documentation if needed?

---

# Final Coding Principle

IdentityCore code should be boring, clear, secure, and predictable.

Clever code is less valuable than code that another engineer can safely understand, test, audit, and maintain.
