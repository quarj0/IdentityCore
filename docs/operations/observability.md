# Operational telemetry

Enable `IDENTITYCORE_TELEMETRY_ENABLED=1` and set
`OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318` for API, Celery and AI.
Set `IDENTITYCORE_SERVICE_NAME=identitycore-worker` on workers and
`identitycore-operations` on the independent operations process. Run
`python manage.py collect_operational_metrics` independently of Celery. The
API/AI startup installs exporters; collector outages do not gate processing.
Use `IDENTITYCORE_TRACE_SAMPLE_RATIO=1` only for an isolated synthetic drill;
the normal sampling ratio is 0.1. OTLP credentials belong in a secret manager.

Start the private example collector/Prometheus/Tempo/Alertmanager stack with
`docker compose -f ops/observability/compose.yaml up -d`. Join backend services to
its network and use its private collector hostname. Host-only synthetic drills
can use `http://127.0.0.1:4318`. Bindings are loopback; never publish these ports
as applicant-facing endpoints. Configure mTLS/private networking, access
controls, persistent encrypted disks and an approved alert receiver before
production. Tempo retains traces for 24 hours; set an approved metrics retention
period with Prometheus deployment flags.

Import `ops/observability/dashboard.json` into Grafana with a Prometheus data
source whose UID is `identitycore-prometheus`. It covers API latency/availability,
processing reliability/latency, provider, webhook, storage and durable queue age.
Configure Tempo as a separate data source to search the `X-Trace-Id` returned by
a sampled API request. The same trace links Celery work, provider invocation,
internal AI processing and object reads. No trace context is sent externally.
Only fixed component/operation, production/sandbox/unknown and success/error
appear as telemetry dimensions. Request payloads, exception messages, URLs,
object keys, applicant identifiers and baggage are excluded.

Validate alerts with:

```sh
docker run --rm --entrypoint promtool \
  -v "$PWD/ops/observability:/rules:ro" -w /rules \
  prom/prometheus:v3.15.0 check rules alerts.yaml
docker run --rm --entrypoint promtool \
  -v "$PWD/ops/observability:/rules:ro" -w /rules \
  prom/prometheus:v3.15.0 test rules alerts.test.yaml
```

See [SLOs and runbooks](slo-alerts.md). Tests cover above/below the critical burn
threshold, the short/long window recovery condition, sandbox exclusion and
stopped-worker queue age. Add a synthetic notification exercise to each
environment's approved pilot-readiness evidence; repository rule tests cannot
prove a private production pager integration.

Random process-instance dimensions distinguish replicas and forked worker counters; their cardinality is bounded by deployed processes, never applicants.
