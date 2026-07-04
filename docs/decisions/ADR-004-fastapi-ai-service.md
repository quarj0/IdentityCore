# ADR-004: Dedicated FastAPI AI Service

**Status:** Accepted

**Date:** 2026-07-04

---

# Context

IdentityCore performs computationally intensive AI operations including:

- Face detection
- Face alignment
- Face embedding generation
- Face matching
- Passive liveness detection
- Active liveness verification
- Document quality analysis
- Optical Character Recognition (OCR)
- Document classification

These workloads differ significantly from traditional web application workloads.

The platform requires an architecture that isolates AI processing while allowing the core business application to remain focused on identity verification workflows.

---

# Decision

IdentityCore will implement AI capabilities as a **separate FastAPI service**.

The Django backend will remain the primary application responsible for business logic, while the FastAPI AI service will provide specialized AI processing through internal APIs.

The AI service will **not** be publicly accessible.

---

# Responsibilities

## Django Backend

Responsible for:

- Authentication
- Authorization
- Tenant isolation
- Verification workflows
- Verification Policies
- Consent management
- Audit logging
- API management
- Webhook delivery
- Decision Engine
- Database persistence

---

## FastAPI AI Service

Responsible for:

- Face detection
- Face alignment
- Face embeddings
- Face matching
- Passive liveness
- Active liveness
- OCR
- Document classification
- Document quality analysis
- AI model version reporting

The AI service produces technical evidence only.

---

# Processing Flow

```id="qmh0fv"
Verification Subject

        ↓

Django Backend

        ↓

Encrypted Object Storage

        ↓

Celery Task

        ↓

FastAPI AI Service

        ↓

AI Results

        ↓

Django Decision Engine

        ↓

Verification Decision
```

The Django backend remains the system of record.

---

# Why FastAPI?

FastAPI was selected because it provides:

- Excellent performance
- Native asynchronous support
- Strong typing with Pydantic
- Automatic OpenAPI documentation
- Simple deployment
- Excellent support for AI and machine learning workloads

It integrates naturally with Python AI libraries already planned for IdentityCore.

---

# Why Not Django?

Django excels at:

- Business logic
- Authentication
- Administration
- ORM
- APIs
- Transactions

However, AI inference workloads have different characteristics:

- Long-running processing
- High CPU usage
- Optional GPU usage
- Model loading
- Specialized dependencies

Separating AI reduces complexity within the Django application.

---

# Service Communication

Communication between Django and the AI service occurs through authenticated internal HTTP requests.

Characteristics:

- Private network communication
- TLS where applicable
- Request validation
- Structured responses
- Request correlation IDs
- Timeouts
- Retry strategy

The AI service is never called directly by external clients.

---

# AI Output

The AI service returns technical evidence.

Examples:

```json id="2mzuhh"
{
  "face_match_score": 0.94,
  "liveness_score": 0.91,
  "ocr_confidence": 0.97,
  "document_quality": 0.89,
  "model_version": "v1.0.0"
}
```

The AI service must never return:

- Verified
- Rejected
- Manual Review Required

Those decisions belong exclusively to the Django Decision Engine.

---

# Model Independence

AI models should be replaceable without modifying business logic.

Example:

```id="8mjlwm"
InsightFace

↓

Future Model

↓

Commercial Provider

↓

Custom Model
```

As long as the AI API contract remains stable, the backend should not require changes.

---

# Scalability

The AI service should scale independently from Django.

Examples:

- Multiple AI workers
- GPU-enabled nodes
- Dedicated OCR workers
- Separate inference queues

This allows AI workloads to grow without affecting API responsiveness.

---

# Failure Handling

AI failures should not crash the platform.

Examples:

- OCR timeout
- Face detection failure
- Model loading failure
- GPU unavailable
- Invalid image

The backend should:

- Retry where appropriate
- Return meaningful errors
- Trigger manual review when necessary
- Record audit events

---

# Security

The AI service must:

- Reject malformed requests
- Validate media types
- Enforce file size limits
- Authenticate requests from Django
- Log safely
- Never expose biometric templates
- Never expose raw model internals

The AI service is an internal component and should not be internet-facing.

---

# Consequences

## Positive

- Clear separation of concerns.
- Independent scaling.
- Easier model replacement.
- Smaller Django codebase.
- Simpler AI dependency management.
- Better operational flexibility.
- Easier performance tuning.

## Negative

- Additional service to maintain.
- Network communication overhead.
- More deployment complexity.
- Additional monitoring requirements.

These trade-offs are acceptable because AI workloads differ significantly from traditional web application workloads.

---

# Alternatives Considered

## AI Inside Django

Rejected because it mixes business logic with computational AI workloads, increases dependency complexity, and makes independent scaling difficult.

---

## Separate Microservice for Every AI Capability

Rejected because it introduces unnecessary operational complexity for Version 1.0.

A single AI service provides sufficient modularity while remaining operationally simple.

---

## External AI-Only Providers

Rejected as the primary approach because:

- Higher operational costs.
- Vendor lock-in.
- Reduced control over sensitive biometric processing.
- Data sovereignty concerns.

External providers may be used as optional fallback providers where appropriate.

---

# Future Considerations

Future versions may include:

- GPU inference clusters.
- Model registry service.
- Model version routing.
- Batch inference.
- Multiple AI services for specialized workloads.
- Federated model deployment.

These enhancements should preserve the existing API contract between Django and the AI service.

---

# Implementation Notes

- FastAPI is an internal service.
- Django remains the system of record.
- AI processing should occur asynchronously through Celery.
- All AI responses should include model metadata.
- AI service contracts should remain backward compatible.

---

# References

- AI Design
- Architecture
- Deployment
- Security
- API Specification
- Testing Strategy
