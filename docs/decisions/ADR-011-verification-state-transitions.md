# ADR-011: Verification state transitions

## Decision

Verification status changes are applied through the locked transition service in
`apps.verifications.transitions`. The service locks the verification row, rejects
invalid transitions, and treats a repeated transition to the current state as an
idempotent no-op.

Terminal states are `verified`, `rejected`, `expired`, `cancelled`, and `failed`.
They cannot transition to another state.

The supported workflow is:

```text
created -> pending_consent
pending_consent -> in_progress | cancelled | expired | failed
in_progress -> awaiting_document | awaiting_selfie | processing |
              manual_review_required | cancelled | expired | failed
awaiting_document -> awaiting_selfie | processing | manual_review_required |
                     cancelled | expired | failed
awaiting_selfie -> awaiting_document | processing | manual_review_required |
                  cancelled | expired | failed
processing -> awaiting_document | awaiting_selfie | manual_review_required |
              verified | rejected | cancelled | expired | failed
manual_review_required -> verified | rejected | failed
```

Terminal transitions record `completed_at` atomically with the status change.
Audit events are emitted by the calling workflow after the transition succeeds,
so the event observes the committed decision state in a stable order.

## Consequences

- Concurrent workers serialize on the verification row instead of overwriting one
  another's state.
- Retries do not create a second state change when the requested state is already
  current.
- New workflow states must be added to the transition table and covered by tests
  before they can be used in production code.
