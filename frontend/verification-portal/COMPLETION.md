# Verification portal maturity and release boundary

Last reviewed: 2026-10-20

The hosted applicant journey is implemented with repository acceptance coverage.
Historical remediation is merged in #433; the
[audit reconciliation](../../docs/reviews/README.md) has no pending/actionable
findings in its snapshot. #281 awaits the published reconciliation receipt.
Repository completion does not establish deployment or biometric certification.

## Implemented paths

- Immutable, locale-specific consent; required document sides; capture/upload validation;
  selfie and policy-selected liveness; processing, review and terminal states.
- Fragment-to-HttpOnly session exchange, same-origin mutations, session-bound route
  allowlists, bounded streamed uploads, upstream timeouts and safe request IDs.
- Camera/recorder cleanup, permission/interruption recovery, supported codecs,
  active-video capture and desktop-to-mobile handoff.
- English/Arabic controlled journey, shell and fallback copy; RTL, translated theme/skip
  controls, country names and consent-to-result accessibility fixtures. Supplied custom
  organization/provider text retains its language.
- Legacy outcome URLs render the authenticated session flow; suffixes cannot assert results.
- Tenant branding and configured safe return destinations.
- Signed hosted subject metadata with explicit ingress trust and unavailable-IP semantics.
- Non-root standalone image, liveness and runtime readiness.
- Chromium/WebKit desktop/mobile journey fixtures plus real HTTP and browser transport
  checks through the standalone BFF with only its upstream replaced by a fixture.

The original acceptance issues [IC-081](https://github.com/quarj0/IdentityCore/issues/224),
[IC-082](https://github.com/quarj0/IdentityCore/issues/225),
[IC-083](https://github.com/quarj0/IdentityCore/issues/226),
[IC-084](https://github.com/quarj0/IdentityCore/issues/227),
[IC-085](https://github.com/quarj0/IdentityCore/issues/228) and
[IC-086](https://github.com/quarj0/IdentityCore/issues/229) are closed in the tracker.
Their closure is not a disposition for later historical findings. Follow the current
register and protected remediation evidence rather than treating these issue IDs as
perpetually open or declaring every related behavior complete.

## Remaining release evidence

A release still requires deployed portal/Django/storage/worker/provider/webhook
integration; a supported physical iOS/Android matrix; approved consent, retention and
residency; representative biometric/PAD evaluation; independent security/privacy/WCAG
assessment; real monitoring, paging, restoration and rollback; pilot cohort results;
and accountable go-live approval.

Read [production operations](../../docs/operations/verification-portal-production.md),
[subject attribution](../../docs/operations/subject-metadata.md) and
[release evidence](../../docs/operations/release-evidence-gate.md) for exact boundaries.
Synthetic browser fixtures do not certify physical cameras, provider accuracy or a
particular deployment.

The merged historical accessibility remediation consolidates duplicate applicant
coverage, scans captured and live-camera states, exercises QR/terminal paths and
uses sequential keyboard navigation. See the [validation procedure](../../docs/operations/accessibility-validation.md).
Its implementation and automated evidence were reviewed and merged in #433;
independent WCAG and assistive-technology validation remain release gates.
