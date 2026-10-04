# Pilot operational load gate

The provisional workload is **30 verification journeys per minute** with a
separate **20 simultaneous applicant burst**. These values are an engineering
baseline until the pilot owner supplies the deployment target. Both API processes receive authenticated read warmup requests before the
capacity measurement; cold starts are measured separately. Burst and steady
phases run sequentially so the concurrency claim is explicit. Journey timing
includes dispatch delay; an overloaded client executor cannot hide queued work.

Each journey uses the public HTTP routes to create a session, accept consent,
upload three approximately 1.1 MB synthetic JPEGs through signed S3 URLs,
complete document and biometric processing, make an independent human decision,
read the committed result and verify cross-tenant denial. Two tenants have their
own production projects and signed webhook receivers. PostgreSQL 17, Redis,
Gunicorn, Celery and the HTTP S3 transport are real; the AI receiver reads the
stored objects and returns deterministic synthetic results after a configured
delay. The storage service is Moto, which does not reproduce production IAM,
network latency, bandwidth ceilings or provider inference capacity.

## Reproduce

Use a fresh, dedicated fixture stack; the harness refuses an existing
`identitycore_load` database. Never point it at an application deployment.

```sh
python scripts/prepare_operational_drill.py --directory /tmp/identitycore-drill
docker compose --env-file /tmp/identitycore-drill/drill.env \
  -p identitycore-drill -f ops/drills/compose.yaml up -d --wait
uv run --project backend python scripts/run_operational_load.py \
  --env-file /tmp/identitycore-drill/drill.env --report /tmp/load-report.json \
  --duration-seconds 60 --rate-per-minute 30 --concurrency 20 --burst
```

Add `--telemetry` when the private collector from the observability runbook is
running. The retained local pilot evidence uses enabled telemetry. CI runs the
same load gate after the isolated restore drill and retains its payload-free
report for 90 days. Destroy only the named synthetic compose project and volumes
when finished. Credentials, presigned URLs, object keys, IDs and media are not
included in the report; restricted temporary process logs are removed on exit.

## Gates and capacity assumptions

Require p95 session creation and human decision response within two seconds,
upload within five seconds, document and biometric processing each within 30
seconds, complete journey within 60 seconds, and dispatch wait within two
seconds. Require every offered journey to finish, no exhausted or unfinished
processing jobs, every webhook delivered with both signatures checked, valid
audit chains, persisted human decisions, published JSON/PDF evidence and the
manual outcome in each decrypted JSON report. Any failed check exits nonzero and
blocks the CI gate. Report offered rate separately from completion throughput
including the finite run's drain tail.

The tested application configuration is two Gunicorn processes with eight
threads each and four Celery threads. Budget at least 22 database connections for this
layout plus monitoring and maintenance; set a deployment-specific connection
ceiling. The fixture uses the default per-request database connection lifecycle. Record CPU affinity and cgroup quota:
this workspace exposes three CPUs but has a two-CPU quota shared with fixtures
and telemetry. Provision at least the measured resources and repeat a longer
steady test on deployment hardware with realistic provider latency and storage.
Do not infer production AI capacity from the 100 ms synthetic default.

Fixture quotas are deliberately 10,000 requests/minute per client, session and
reviewer. Production defaults remain unchanged and are much lower; configure
approved request budgets before expecting this verification arrival rate.
The baseline polls `/sessions/{id}/status` every 3.5 seconds, matching the
verification portal. Use `--poll-mode partner --poll-interval-seconds 0.4` to
reproduce the deliberately heavier partner-read stress test. Polling cadence,
upload bandwidth, provider concurrency and model latency all
consume separate capacity. Maintain queue age below the SLO and stop a ramp on
latency failures, retry exhaustion, audit failures or outbox growth. Re-run with
higher arrival/concurrency values to identify the first failing gate; traffic
above the measured passing envelope is unsupported until retested.

## Deployment of decision safeguards

Drain API writers and all processing/retention workers before applying migration
0019 and restarting every writer on the new version. The revision column has a
database default for older inserts, but an old worker still lacks the conflict
guard; do not mix old and new decision writers during rollout. Review conflict
audit events rather than retrying a stale automatic decision over a human result.

## Findings addressed

The initial 30/minute run failed session, upload, review and journey latency.
Subsequent concurrency exposed joined tenant/project locks causing foreign-key
commit deadlocks and concurrent audit appends producing broken links. Locks now
cover only the changed rows; audit appends serialize with an explicit ordering
before webhook endpoint locks. Successful legacy bearer proofs are bounded and
coalesced per process, and generated 256-bit session tokens use constant-time
digest verification. Human decisions can consume automatic review routes, and
stale workers cannot overwrite human proposals or terminal outcomes. ADR-029
records these choices and their authentication and PostgreSQL race regressions.

For payload-free function timing diagnosis, use `--profile-report /tmp/functions.jsonl`
in a separate run. This optional fixture middleware records only fixed operation
labels, function locations, call counts and timings. Profiling adds overhead and
its results must not be used as passing capacity evidence.

## Retained measurements (2026-10-04)

The [passing portal-aligned report](evidence/2026-10-04-load.json) completed
20 burst journeys followed by 30 sustained journeys, including 150 uploads and
100 signed webhook deliveries. Telemetry was enabled. P95 session creation was
1.717 seconds, upload 3.425 seconds, document processing 8.240 seconds, biometric
processing 11.468 seconds, human decision response 1.173 seconds, full journey
31.341 seconds and client dispatch wait 0.034 seconds. All correctness gates
passed. This is a short orchestration baseline, not a production soak or model
capacity certificate.

The [original failed run](evidence/2026-10-04-load-before.json) records the
pre-fix sustained workload. The [post-fix stress report](evidence/2026-10-04-load-stress.json)
uses full partner reads every 400 ms with the 20-applicant burst: all 50 journeys
completed with valid audit chains and preserved human decisions, but p95 session
creation (2.130 seconds) and review response (2.832 seconds) breached the same
limits. That polling cadence is outside the measured passing envelope on this
shared two-CPU budget. Increase resources or reduce full partner polling before
admitting that traffic; retain the same latency gates when retesting.
