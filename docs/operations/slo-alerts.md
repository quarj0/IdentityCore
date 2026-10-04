# Production SLOs and alert response

These initial 30-day objectives protect the pilot. Service owners must approve
changes in a tracked change record; changing a threshold to hide an incident is
not permitted. Run `promtool test rules ops/observability/alerts.test.yaml` from
`ops/observability` (or use the container command in observability.md).

| SLI | Objective | Denominator / bad event |
| --- | --- | --- |
| API availability | 99.9% | authenticated environment-scoped responses / HTTP 5xx |
| Automated processing reliability | 99% | committed completed or exhausted jobs / exhausted jobs |
| Provider execution | 99% | attempted checks / exceptions including timeouts |
| Webhook transport | 99% | outbound attempts / network or non-success HTTP errors |
| Storage operations | 99.9% | object operations / exceptions |
| Processing latency | 95% within 120 seconds | durable job creation to committed terminal processing result |
| Queue freshness | no work older than 300 seconds | oldest pending durable processing job or webhook |

A business decline or human-review outcome is not a reliability failure.
Processing counters are job-based (document and biometric jobs), not applicant
completion or model accuracy. HTTP metrics include only trusted project-scoped
production traffic; unknown public/authentication and health traffic are visible
but excluded from tenant processing SLOs. Metrics are unsampled.

Page on a 14.4x burn in **both** the last hour and last five minutes, sustained
two minutes. Warn on a 6x burn in both six hours and thirty minutes, sustained
fifteen minutes. For a 30-day window, those consume approximately 2% of the
budget in one hour and 5% in six hours. Zero traffic produces zero burn. The
latency warning requires twenty completed jobs to avoid unstable tiny cohorts.
Independent queue age and missing-exporter alerts catch stopped workers even
when there are no completed jobs to populate a rate.

Sandbox and unknown environments never page these production objectives.
Before maintenance, create an Alertmanager silence with `service=identitycore`
and `environment=production`, a specific change reference, owner, and bounded
expiry. Keep metrics and rule evaluation running; silence notifications rather
than changing outcomes or disabling monitoring. Verify silence expiry and
recovery after the change. Alertmanager inhibits corresponding warnings while
critical alerts are active. The supplied receiver has no destination: configure
and exercise the approved on-call receiver before pilot approval.

## API

Check deployment health, database saturation and release timing. Use a trace ID
from a synthetic request to inspect the API/worker chain. Roll back a correlated
release through the approved change record; do not disable tenant authorization.
Escalate database connectivity/saturation to the service owner.

## Processing

Follow [processing-job recovery](processing-job-recovery.md). Check oldest work,
leases, worker availability and provider response latency. Recover only stale
jobs using the supported command; preserve committed decisions and evidence.

## Provider

Follow [provider resilience](provider-route-resilience.md). Check timeout/circuit
state and capability routing; use approved fallback or manual review. Do not
bypass residency or tenant/provider assignment requirements.

## Webhook

Follow [incident response](incident-response.md) webhook replay instructions.
Check queue age, receiver health and signatures, then use supported replay.
Delivery is at least once; confirm receiver idempotency before replaying.

## Storage

Check storage availability, encryption grants and regional endpoint health.
Follow retention recovery instructions in [incident response](incident-response.md).
Do not bypass encryption or deletion holds to clear an alert.

## Monitoring

Check the operations exporter, collector, Prometheus scrape and database access.
Restart the failed component, confirm heartbeat freshness and test an alert with
synthetic input. Treat missing telemetry as loss of operational visibility and
pause a traffic ramp until the monitoring path recovers.
