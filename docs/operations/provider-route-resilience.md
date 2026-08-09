# Provider Route Resilience

## Purpose

Provider routes execute with a published policy for timeout, bounded attempts, circuit
opening and recovery, ordered fallback, and the final verification action. These controls
are scoped to the route's tenant, environment, capability, and immutable version.

## Runtime behavior

For each provider step, the runtime:

1. skips the step when its circuit is open and the recovery deadline has not passed;
2. passes `timeout_seconds` to the adapter, which must enforce it at the I/O boundary;
3. retries only exceptions whose normalized contract declares `retryable: true`;
4. stops at `max_attempts_per_provider` and selects the next route step;
5. records every invocation or circuit skip under one `pex_` execution ID; and
6. applies `manual_review` or `fail` after the route is exhausted.

Attempt history contains provider and route identifiers, sequence, attempt number, outcome,
timeout, safe error code, retryability, and fallback reason. It must never contain raw
provider responses, credentials, signed URLs, document data, or biometric data.

## Circuit recovery

Retryable failures increment the route step's consecutive-failure count. At the configured
threshold the circuit opens until `retry_after`. The first caller after that deadline
atomically changes the state to half-open and owns the recovery probe. Other callers skip
that provider until the probe completes. A successful probe closes and resets the circuit;
a retryable failure opens it for another recovery interval.

Operators should investigate repeatedly opening circuits through safe attempt error codes
and provider-level health metrics. Do not manually delete attempt history to force recovery.
If an urgent reset is operationally necessary, use an audited administrative procedure that
sets the circuit to closed, clears the failure count, and documents the provider incident.

## Health inspection

Tenant operators can inspect a route without provider secret access:

```text
GET /api/v1/providers/health/?environment=sandbox&window_hours=24
```

Use the environment and time window shown in the response scope when correlating an
incident. Availability is successful terminal checks divided by terminal checks; error
rate is failed or timed-out terminal checks divided by terminal checks. Latency p50 and
p95 use nearest-rank values from checks that recorded a duration. Pending, processing,
and cancelled checks do not affect these rates.

The route section reports the published route version, ordered steps, and current circuit
state. `open` with a future retry time means calls will skip that step. `half_open` means a
single recovery probe is in flight. Compare scoped provider rates with circuit state and
safe error-code counts; provider payloads and free-form error messages are intentionally
unavailable in this view.

## Failure handling

`manual_review` is the safe default and creates a system decision with reason code
`provider_route_exhausted`. `fail` is appropriate only where policy explicitly permits a
provider outage to terminate the verification. Neither outcome can approve a verification.
