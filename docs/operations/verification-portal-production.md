# Verification portal production operations

Last reviewed: 2026-08-09

The repository-owned portal is a working vertical slice with acceptance work tracked in
IC-081 through IC-086 and summarized in
`frontend/verification-portal/COMPLETION.md`. The gates in this document are additional
deployment- and human-owned release evidence; completing repository issues does not satisfy
them automatically.

The verification portal is releasable only when every gate below has an owner,
dated evidence, and approval. Repository tests are necessary but do not replace
independent assessment or a physical-device pilot.

## Service-level objectives

| Signal                     | Target                         | Page when                                |
| -------------------------- | ------------------------------ | ---------------------------------------- |
| BFF availability           | 99.95% over 30 days            | 5-minute success rate below 99%          |
| Session exchange latency   | p95 below 750 ms               | p95 above 1.5 s for 10 minutes           |
| Evidence upload initiation | 99.5% successful               | failures above 2% for 10 minutes         |
| Journey completion         | Baseline set by approved pilot | 20% relative regression by locale/device |
| Provider latency           | Contract-specific              | timeout/error budget exhausted           |

Logs and traces must contain a generated request ID, route template, status,
latency, deployment version, and provider-check ID where applicable. They must
never contain bearer cookies, handoff codes, consent content, document fields,
media, biometric templates, signed upload URLs, or request bodies.

## Release evidence gates

- Policy fixtures demonstrate passive, active, retry, expiry, and review flows.
- Every supported locale has complete catalogs; an RTL locale passes visual,
  keyboard, screen-reader, and axe checks.
- WebKit and Chromium pass in CI; the supported physical iOS and Android matrix
  has signed results covering permissions, orientation, interruption, and codecs.
- The biometric provider adapter has security, privacy, residency, retention,
  anti-spoof, demographic-performance, timeout, replay, and failover evidence.
- Independent penetration, WCAG, privacy, and biometric reports have no open
  critical/high findings; accepted residual risks name an accountable executive.
- A limited pilot meets its approved completion, abandonment, false-reject,
  inconclusive, and support thresholds for every supported locale/device cohort.

## Incident response

Use the [incident response and breach triage runbook](incident-response.md) for
severity, role assignment, evidence custody, containment, notification
decisions, recovery, exercises, and post-incident review. Its scenario playbooks
cover credential exposure, biometric/provider incidents, tenant isolation,
availability/data integrity, and consent mismatch.
