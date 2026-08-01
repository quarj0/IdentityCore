# Verification portal completion boundary

**Repository implementation status: complete.**

This status means the work that can be implemented and continuously verified in
this repository is present. It does not claim that a particular deployment,
biometric provider, legal program, or fleet of physical devices has been
certified. Those activities require accountable humans and deployment-specific
evidence.

## Completed in the repository

- The subject journey covers immutable consent, required document sides,
  selfie capture, policy-selected passive or active liveness, processing,
  manual-review and terminal states, upload retry, and desktop-to-mobile handoff.
- Session bearer credentials are exchanged from the URL fragment into secure,
  same-origin, `HttpOnly`, `SameSite=Strict` BFF cookies and are never persisted
  by browser code.
- BFF routes enforce same-origin mutation, bind requests to the authenticated
  session, allow only verification endpoints, cap request sizes, apply upstream
  timeouts, reject redirects, propagate safe request IDs, and return no-store
  responses without exposing upstream credentials.
- Organization return URLs and logos are constrained to safe configured origins.
- Camera and recorder lifecycles handle permission denial, interruption,
  unmounting, codec negotiation, duration limits, size limits, and retakes.
- English and Arabic locale direction/consent architecture is present. Adding a
  locale is a release change and requires the evidence listed below.
- The standalone container runs as a non-root user and exposes separate liveness
  and runtime-configuration readiness endpoints.
- CI installs Chromium and WebKit and runs lint, production builds, type checks,
  security assertions, accessibility checks, and desktop/mobile journey tests.

## Human and deployment release gates

Do not reopen the portal implementation merely because the following evidence is
deployment-specific. Record it in the release system with an owner, date,
environment, result, evidence link, and approver.

- [ ] **Production configuration:** provision the public HTTPS origin,
  server-only HTTPS `API_ORIGIN`, exact organization return-origin allowlist,
  deployment version, secrets, DNS, certificates, HSTS, proxy upload/time limits,
  and exact object-storage CORS origins.
- [ ] **End-to-end environment:** certify the deployed portal with real Django,
  storage, workers, provider adapters, webhook delivery, manual review, retention,
  expiry, retry, outage, and rollback behavior.
- [ ] **Physical devices:** sign results for the supported iOS and Android matrix,
  including permissions, camera selection, orientation, background/foreground
  interruption, low bandwidth, codecs, and desktop-to-mobile handoff.
- [ ] **Provider assurance:** approve security, privacy, residency, retention,
  anti-spoof, replay, demographic-performance, timeout, circuit-breaker, and
  failover evidence for the exact provider/model configuration.
- [ ] **Independent assurance:** close or formally accept findings from
  penetration, WCAG, privacy, legal/consent, and biometric assessments.
- [ ] **Operations:** demonstrate redacted logs/traces, request correlation,
  SLO dashboards, paging, rollback, affected-session queries, support ownership,
  and credential-exposure/provider-outage exercises.
- [ ] **Pilot:** approve cohort thresholds and complete a limited pilot measuring
  completion, abandonment, false reject, inconclusive, manual-review, and support
  rates by locale, browser, and device.
- [ ] **Final approval:** security, privacy/legal, accessibility, product,
  operations, and the accountable business owner approve release evidence.

The detailed SLOs, prohibited telemetry, evidence requirements, and incident
process remain authoritative in
`docs/operations/verification-portal-production.md`.
