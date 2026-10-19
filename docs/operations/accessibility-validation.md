# Accessibility validation

Run browser checks against production builds. The applicant suite uses desktop
Chromium/WebKit and Pixel/iPhone browser profiles; these profiles do not certify
physical cameras, assistive technologies or operating-system permissions.

From `frontend/`:

```bash
pnpm --filter verification-portal test:e2e critical-subject-accessibility.spec.ts critical-terminal-handoff-accessibility.spec.ts
pnpm --filter verification-portal exec playwright test --config=playwright.platform-admin.config.ts --grep 'review queue and decision flow'
```

The applicant specs consolidate the earlier duplicate `critical-accessibility`
journey into the English/Arabic subject suite. Desktop controls are reached through
actual Tab navigation and activated by keyboard, including native file selection;
mobile controls use touch. A visible/enabled control is required before activation.
The handoff chooser is awaited before scanning, rather than scanning a loading page.

Axe scans the mounted consent, document/selfie capture and captured-image review,
live camera, recording and recording-review states, plus manual review, verified
and failed outcomes. Desktop QR checks create the grant, inspect the named code,
copy its exact link and scan the waiting state. The initiating chooser is
intentionally absent from mobile tests; mobile capture and terminal panels still
run. Synthetic media/transport fixtures exercise application behavior, not biometric
accuracy or real provider responses.

The reviewer scenario includes submitted supporting evidence, opens it through the
keyboard, enters review notes and scans the approved state. Its backend fixture
retains the resulting decision across refreshes.

The shared helper enables WCAG 2 A/AA, 2.1 A/AA and 2.2 AA rule tags and fails on
serious or critical violations. Axe is injected with the current response nonce;
CSP stays enforced. Scans wait for short control color transitions to settle while
recording progress and activity indicators remain active. Do not replace sequential
focus checks with programmatic focus, disable rule tags, bypass CSP, or skip entire
mobile journeys to obtain a passing result.

Record the commit, production build, browser versions, scenario results and defects
with the release evidence. Manual screen-reader, keyboard/touch and physical-device
assessment, independent WCAG review and deployment validation remain release work;
passing automated scans is not an accessibility certification.
