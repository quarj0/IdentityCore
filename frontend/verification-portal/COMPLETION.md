# Verification portal maturity and release boundary

Last reviewed: 2026-08-09

**Repository implementation status: working vertical slice with open acceptance work.**

The primary subject journey and its security foundation are implemented, but repository
acceptance work remains tracked in IC-081 through IC-086. Separately, no repository result
can certify a particular deployment, biometric provider, legal program, or fleet of
physical devices; those gates require accountable humans and deployment-specific evidence.

## Implemented foundations

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
- Camera and recorder lifecycles include permission, interruption, unmounting, codec,
  duration, size, and retake handling. IC-082 remains open until predictable recovery and
  preservation behavior pass the required browser/device matrix.
- English and Arabic locale direction and consent architecture is present. IC-083 remains
  open until the complete applicant journey, formatting, fallback, and RTL behavior pass
  automated acceptance checks in at least two configured locales.
- The standalone container runs as a non-root user and exposes separate liveness
  and runtime-configuration readiness endpoints.
- CI installs Chromium and WebKit and runs lint, production builds, type checks, security
  assertions, landing-page accessibility checks, and mocked desktop/mobile journey tests.

## Repository acceptance work

- **IC-081:** keyboard and WCAG checks across consent, upload, camera, handoff, review, and
  decision journeys.
- **IC-082:** predictable camera denial, interruption, and unsupported-device recovery.
- **IC-083:** a complete applicant journey in at least two configured locales, including
  RTL and fallback tests.
- **IC-084:** safe tenant branding upload and accessible color validation.
- **IC-085:** standardized API errors, correlation IDs, bounded retries, and expired-session
  behavior.
- **IC-086:** deterministic Playwright coverage from organization setup through delivered
  result, including review, failure, handoff, and webhook-visible states.

Close these items only from their acceptance evidence; the presence of related components
does not make the portal repository-complete.

## Human and deployment release gates

The following gates are deployment-specific and do not replace the repository acceptance
work above. Record each with an owner, date, environment, result, evidence link, and
approver.

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
