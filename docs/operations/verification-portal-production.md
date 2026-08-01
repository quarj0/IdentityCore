# Verification portal production operations

The repository-owned portal implementation is marked complete in
`frontend/verification-portal/COMPLETION.md`. The gates in this document are
deliberately deployment- and human-owned release evidence; they do not indicate
unfinished frontend code.

The verification portal is releasable only when every gate below has an owner,
dated evidence, and approval. Repository tests are necessary but do not replace
independent assessment or a physical-device pilot.

## Service-level objectives

| Signal | Target | Page when |
| --- | --- | --- |
| BFF availability | 99.95% over 30 days | 5-minute success rate below 99% |
| Session exchange latency | p95 below 750 ms | p95 above 1.5 s for 10 minutes |
| Evidence upload initiation | 99.5% successful | failures above 2% for 10 minutes |
| Journey completion | Baseline set by approved pilot | 20% relative regression by locale/device |
| Provider latency | Contract-specific | timeout/error budget exhausted |

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

1. **Credential exposure:** revoke affected sessions, disable link issuance,
   preserve redacted audit evidence, rotate signing material if implicated, and
   notify security/privacy leads.
2. **Biometric/provider incident:** open the circuit, route to the certified
   fallback or manual review, stop automatic rejection, and preserve provider
   check identifiers without copying biometric payloads.
3. **Completion regression:** halt rollout, segment by deployment, locale,
   browser, device and workflow, then roll back if the error budget is exceeded.
4. **Consent mismatch:** stop new sessions for the affected tenant/locale,
   preserve template versions and acceptance records, and require re-consent
   where privacy/legal owners determine it is necessary.

Every incident needs a commander, communications owner, privacy/security owner,
timeline, affected-session query, rollback decision, and blameless review. Run
credential-exposure and provider-outage exercises before the first pilot and at
least twice yearly thereafter.
