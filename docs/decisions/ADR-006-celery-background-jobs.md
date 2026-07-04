# ADR-006: Celery for Background Processing

**Status:** Accepted

**Date:** 2026-07-04

---

# Context

IdentityCore performs many operations that should not execute during an HTTP request.

Examples include:

- AI processing
- OCR
- Face matching
- Liveness detection
- Email delivery
- Webhook delivery
- Audit exports
- Cleanup jobs
- Scheduled maintenance
- Future report generation

Executing these operations synchronously would:

- Increase API latency.
- Reduce scalability.
- Cause request timeouts.
- Create a poor user experience.
- Increase infrastructure costs.

The platform requires a reliable background job processing system.

---

# Decision

IdentityCore will use **Celery** as its background task processing framework.

Redis will serve as the broker for Version 1.0.

Background jobs will be executed asynchronously by dedicated Celery workers.

---

# Responsibilities

Celery is responsible for:

- AI processing
- OCR processing
- Face matching
- Liveness processing
- Webhook delivery
- Email notifications
- Scheduled cleanup
- Expired verification handling
- Retention enforcement
- Future reporting tasks

Celery is **not** responsible for:

- Business decisions
- Authentication
- Authorization
- Tenant management
- API request handling

Those responsibilities remain within Django.

---

# Processing Flow

Example verification workflow:

```id="m8zzfy"
Verification Created
        ↓
Store metadata
        ↓
Queue AI Task
        ↓
Celery Worker
        ↓
FastAPI AI Service
        ↓
Store AI Evidence
        ↓
Decision Engine
```

The HTTP request returns quickly while processing continues in the background.

---

# Queue Strategy

Version 1.0 will separate workloads into logical queues.

Example:

```id="8xgk8x"
default

ai_processing

webhooks

notifications

maintenance
```

This separation prevents long-running AI jobs from delaying lightweight tasks such as email or webhook delivery.

---

# Task Design Principles

Every task should be:

- Small
- Focused
- Idempotent where possible
- Safe to retry
- Independently executable
- Observable

Tasks should perform one responsibility only.

---

# Retry Strategy

Transient failures should be retried automatically.

Examples:

- AI service temporarily unavailable.
- Network timeout.
- Email provider unavailable.
- Webhook endpoint offline.

Retries should use:

- Exponential backoff.
- Maximum retry limits.
- Structured logging.

Permanent failures should be recorded and surfaced for investigation.

---

# Idempotency

Tasks must tolerate duplicate execution.

Examples:

- Delivering the same webhook.
- Processing the same AI request.
- Sending the same notification.

Where necessary, tasks should check existing state before performing work.

Idempotent tasks improve reliability during retries and worker failures.

---

# Tenant Context

Every tenant-related task must include tenant context.

Example:

Preferred:

```python id="vbyb8v"
process_verification(
    tenant_public_id,
    verification_public_id
)
```

Avoid:

```python id="z4aw2v"
process_verification(
    verification_id
)
```

Worker execution must never lose tenant isolation.

---

# Error Handling

Task failures should:

- Log structured errors.
- Preserve request correlation IDs where applicable.
- Retry if appropriate.
- Emit audit events when required.
- Avoid exposing sensitive information.

Failures should never leave business data in an inconsistent state.

---

# Scheduling

Periodic jobs will be managed by Celery Beat.

Examples:

- Verification expiry
- Session cleanup
- Retention cleanup
- Failed webhook retry scans
- Maintenance jobs

Only one scheduler instance should be active in production.

---

# Monitoring

Background processing should expose metrics including:

- Queue length
- Processing time
- Retry count
- Failure rate
- Worker availability
- Task duration

Monitoring should allow early detection of queue backlogs and worker failures.

---

# Security

Celery tasks must:

- Validate task inputs.
- Authenticate communication where applicable.
- Respect tenant boundaries.
- Avoid logging sensitive information.
- Never store secrets in task payloads.

Background workers are subject to the same security standards as API services.

---

# Scalability

Workers should scale independently from the Django backend.

Examples:

- Additional AI workers.
- Additional webhook workers.
- Dedicated notification workers.

Scaling should be driven by workload characteristics rather than application size.

---

# Performance

Long-running tasks should never block HTTP responses.

Target behavior:

```id="55xj98"
Client Request

↓

Immediate API Response

↓

Background Processing

↓

Completion Event

↓

Webhook / Polling
```

This keeps API response times predictable.

---

# Consequences

## Positive

- Faster API responses.
- Better scalability.
- Improved user experience.
- Independent worker scaling.
- Reliable retry handling.
- Cleaner separation of concerns.

## Negative

- Additional infrastructure.
- More operational monitoring.
- Eventual consistency in some workflows.
- More complex debugging across asynchronous boundaries.

These trade-offs are acceptable given the performance and reliability benefits.

---

# Alternatives Considered

## Synchronous Processing

Rejected because AI inference, OCR, and webhook delivery are too slow for request-response workflows.

---

## Django Background Threads

Rejected because background threads are unreliable across multiple web server processes and deployments.

---

## RQ

Rejected because Celery provides a richer feature set for scheduling, retries, routing, monitoring, and long-running production workloads.

---

## Distributed Messaging Platforms

Technologies such as Kafka or RabbitMQ were considered.

They were rejected for Version 1.0 because they introduce unnecessary operational complexity for the expected workload.

Redis-backed Celery provides an appropriate balance between simplicity and capability.

---

# Future Considerations

Future versions may evaluate:

- RabbitMQ as the broker.
- Kafka for event streaming.
- Priority queues.
- Dead-letter queues.
- Distributed task tracing.
- Workflow orchestration for complex verification pipelines.

These enhancements should not change the fundamental asynchronous architecture.

---

# Implementation Notes

- Redis is the Celery broker for Version 1.0.
- Celery Beat manages scheduled tasks.
- Long-running operations must execute in workers.
- Tasks should be idempotent whenever practical.
- Worker queues should remain logically separated by responsibility.

---

# References

- Deployment
- Architecture
- AI Design
- Testing Strategy
- Security
- ADR-004: Dedicated FastAPI AI Service
