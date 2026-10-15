# Historical review audit (#281)

The disposition register tracks findings by original PR, comment and thread identifier. A resolved GitHub thread does not establish that its finding was implemented. Completed dispositions cite inspected implementation and regression evidence.

The register includes 823 threads from closed or merged PRs: 168 fixed, 196 verified, 4 actionable and 455 pending individual audit. It extends the original 484-thread scope with subsequent closed-PR feedback. The original issue remains open.

Merged remediation covers OCR outage gates, biometric evidence promotion, submitted-review expiry, MRZ issuer matching, provider attempt/evidence invariants, single-variant OpenCV runtime and authenticated immutable audit records. Current-main validation also covers redaction, secure HTTP adapters and webhook outbox/claim/disable/replay behavior. Delivery-time webhook isolation and controlled provider-health codes are merged in #370 and #372. Additional validation covers decision locks, external-risk I/O, authenticity redaction, retention holds and deferred evidence generation. System fallback contract fixes are merged in #373. Parser fixes are merged in #365. The independent SDK/idempotency audit verifies existing signing, replay, profile, retry and compiler behavior, and tracks live project/example, completion/type and conformance fixes in #375–#377. Conformance fixes are merged in #377; completion fixes are merged in #376. Reproduced adapter-test and partial-decision-contract findings are merged in #380, and generated SDK contract fixes in #381. Platform MFA auditing and public sample-token rejection are merged in #382, including independent AI service startup enforcement.

The policy restriction and local frontend CORS fixes are merged in #387. The session/consent fixes and four valid late review findings are merged in #388, with twelve historical findings and the existing status mapping independently verified. Validation includes actual PostgreSQL challenge-consumption races and all final-head CI/Security checks.

The portal/legacy findings and seven valid late findings are addressed in protected merged PR #389 after final-head review, successful CI/Security, 952 backend tests run with 34 skips, and 104 passing portal browser cases with four skips. The history API reports unavailable legacy locale defaults explicitly without modifying retained acceptance evidence.

The Postman GH national ID audit reproduces the missing back capture and repairs session-authenticated uploads and transfers. A regression executes the checked-in collection payloads and response scripts through the actual consent, upload, document and selfie APIs. The finding and two late reviews are fixed in protected merged PR #390 with actual collection integration validation, final-head review and successful CI/Security.

For each remediation PR, inspect all review threads, implement valid late feedback, reply with commit and validation evidence, request a fresh final-head review, and require successful CI/Security. Refresh threads immediately before merging. Do not close #281 while pending dispositions or actionable findings remain.

Protected merged PR #364 supplies 47 individually inspected dispositions, including six verified existing-code or explicitly accepted policy findings. Its documented mutable-review timing limitation remains an accepted policy decision.

Four historical platform admin findings remain actionable until protected merge: expired invitation replacement, retained tenantless deactivation reasons and the final active administrator concurrency invariant. Regressions cover fresh actor authorization and platform audit integrity; actual PostgreSQL races are required in CI.

Protected merged PR #394 fixes five individually reproduced manual review protocol findings and verifies fourteen related existing behaviors. Its final head passed independent review, all PR/push CI and Security, and the dedicated App gate before trusted merge.

Protected merged PR #396 fixes eleven individually audited workflow publication findings. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; the narrow temporary CI-selector approval was removed after trusted merge.
