# ADR-027: Payload-free operational telemetry

Status: Accepted

Use OpenTelemetry OTLP HTTP for API, Celery, provider, storage and AI spans and
metrics. Export only fixed operation/component names, enumerated environment,
and success/error. Trace IDs are random correlation identifiers; no tenant,
subject, verification ID, URL, object key, arguments, baggage, exception text or
stack is exported. W3C context crosses trusted worker and internal AI boundaries;
external webhooks and providers do not receive it. Sampling defaults to 10%.

An independent database-backed operations process exports queue age, including
when all workers stop. Processing completion counters are emitted after commit.
Telemetry is disabled by default and does not change authentication or decisions.
Collector and trace storage are private infrastructure with short retention.
Metrics are unsampled. Sandbox and unknown traffic cannot page production SLOs.

OTLP exporters use bounded asynchronous buffers and five-second export timeouts.
Monitoring failures must not fail verification requests. Deployment operators
must configure the collector, secure network boundaries and alert destinations.

Random process-instance dimensions distinguish replicas and forked worker counters; their cardinality is bounded by deployed processes, never applicants.
