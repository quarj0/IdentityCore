# Historical review audit (#281)

The disposition register tracks findings by original PR, comment and thread identifier. A resolved GitHub thread does not establish that its finding was implemented. Completed dispositions cite inspected implementation and regression evidence.

The register includes 824 threads from closed or merged PRs: 169 fixed, 198 verified, 11 actionable and 446 pending individual audit. It extends the original 484-thread scope with subsequent closed-PR feedback. The original issue remains open.

Merged remediation covers OCR outage gates, biometric evidence promotion, submitted-review expiry, MRZ issuer matching, provider attempt/evidence invariants, single-variant OpenCV runtime and authenticated immutable audit records. Current-main validation also covers redaction, secure HTTP adapters and webhook outbox/claim/disable/replay behavior. Delivery-time webhook isolation and controlled provider-health codes are merged in #370 and #372. Additional validation covers decision locks, external-risk I/O, authenticity redaction, retention holds and deferred evidence generation. System fallback contract fixes are merged in #373. Parser fixes are merged in #365. The independent SDK/idempotency audit verifies existing signing, replay, profile, retry and compiler behavior, and tracks live project/example, completion/type and conformance fixes in #375–#377. Conformance fixes are merged in #377; completion fixes are merged in #376. Reproduced adapter-test and partial-decision-contract findings are merged in #380, and generated SDK contract fixes in #381. Platform MFA auditing and public sample-token rejection are merged in #382, including independent AI service startup enforcement.

The policy restriction and local frontend CORS fixes are merged in #387. The session/consent fixes and four valid late review findings are merged in #388, with twelve historical findings and the existing status mapping independently verified. Validation includes actual PostgreSQL challenge-consumption races and all final-head CI/Security checks.

The portal/legacy findings and seven valid late findings are addressed in protected merged PR #389 after final-head review, successful CI/Security, 952 backend tests run with 34 skips, and 104 passing portal browser cases with four skips. The history API reports unavailable legacy locale defaults explicitly without modifying retained acceptance evidence.

The Postman GH national ID audit reproduces the missing back capture and repairs session-authenticated uploads and transfers. A regression executes the checked-in collection payloads and response scripts through the actual consent, upload, document and selfie APIs. Its correction is protected merged in #390 after fresh final-head review, successful CI/Security and the dedicated evidence check.

For each remediation PR, inspect all review threads, implement valid late feedback, reply with commit and validation evidence, request a fresh final-head review, and require successful CI/Security. Refresh threads immediately before merging. Do not close #281 while pending dispositions or actionable findings remain.

The workflow publication audit reproduces seven behaviors covering ten historical findings, and identifies the unguarded concurrent version allocation finding separately. The prepared shared publication helper validates steps/settings and lifecycle, preserves tenant ownership, namespaces generated policies, resets edited publications to draft, and allocates versions under a row lock. All eleven findings remain actionable until protected merge, including actual PostgreSQL race validation.

Protected merged PR #364 closes 47 additional feedback threads: 41 implementation, deployment or documentation dispositions and six verified dispositions, including five existing AI/workflow fixes and the owner’s accepted mutable-review timing limitation. The residual timing race remains explicit. All current-head CI/Security and the dedicated evidence check passed before trusted merge.

Five individually inspected template lifecycle findings remain actionable until reviewed protected merge. Backend regressions reproduce slug collision, invalid publication settings and the absent stable-identity version operation; the archived lifecycle guard passed on preceding code. Eight browser cases exercise lifecycle controls and actual new-version navigation in Chromium and WebKit.

Protected merged PR #394 fixes five individually reproduced manual review protocol findings and verifies fourteen related existing behaviors. Its final head passed independent review, all PR/push CI and Security, and the dedicated App gate before trusted merge.

The idempotency CORS concern is independently verified against current defaults, common middleware and the actual API preflight regression. Template mutations refresh active actor permissions under the platform serialization lock and preserve valid tenant-bound or tenantless audit scope; instantiation acquires its audit scope before template counter locks.

Six additional original template form findings are reproduced and remediated locally: successful dialog closure, required checks and usable workflow steps, persisted description edits, and template/workflow operator rationale in authenticated audit metadata. They remain actionable until protected merge. Full backend ran 1000 tests with 36 skips; all twenty corresponding browser cases passed.

Protected merged PR #396 fixes eleven individually audited workflow publication findings. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; the narrow temporary CI-selector approval was removed after trusted merge.

The closed #396 no-op edit review is also recorded as fixed with its strict canonical resolver evidence and protected merge receipt.
