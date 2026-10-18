# Historical review audit (#281)

The disposition register tracks findings by original PR, comment and thread identifier. A resolved GitHub thread does not establish that its finding was implemented. Completed dispositions cite inspected implementation and regression evidence.

860 threads from closed or merged PRs: 237 fixed, 332 verified, 37 actionable and 254 pending individual audit. Actionable findings remain open until their remediation merges; resolution state is not implementation evidence. It extends the original 484-thread scope with subsequent closed-PR feedback. The original issue remains open.

Merged remediation covers OCR outage gates, biometric evidence promotion, submitted-review expiry, MRZ issuer matching, provider attempt/evidence invariants, single-variant OpenCV runtime and authenticated immutable audit records. Current-main validation also covers redaction, secure HTTP adapters and webhook outbox/claim/disable/replay behavior. Delivery-time webhook isolation and controlled provider-health codes are merged in #370 and #372. Additional validation covers decision locks, external-risk I/O, authenticity redaction, retention holds and deferred evidence generation. System fallback contract fixes are merged in #373. Parser fixes are merged in #365. The independent SDK/idempotency audit verifies existing signing, replay, profile, retry and compiler behavior, and tracks live project/example, completion/type and conformance fixes in #375–#377. Conformance fixes are merged in #377; completion fixes are merged in #376. Reproduced adapter-test and partial-decision-contract findings are merged in #380, and generated SDK contract fixes in #381. Platform MFA auditing and public sample-token rejection are merged in #382, including independent AI service startup enforcement.

The policy restriction and local frontend CORS fixes are merged in #387. The session/consent fixes and four valid late review findings are merged in #388, with twelve historical findings and the existing status mapping independently verified. Validation includes actual PostgreSQL challenge-consumption races and all final-head CI/Security checks.

The portal/legacy findings and seven valid late findings are addressed in protected merged PR #389 after final-head review, successful CI/Security, 952 backend tests run with 34 skips, and 104 passing portal browser cases with four skips. The history API reports unavailable legacy locale defaults explicitly without modifying retained acceptance evidence.

The Postman GH national ID audit reproduces the missing back capture and repairs session-authenticated uploads and transfers. A regression executes the checked-in collection payloads and response scripts through the actual consent, upload, document and selfie APIs. The finding and two late reviews are fixed in protected merged PR #390 with actual collection integration validation, final-head review and successful CI/Security.

For each remediation PR, inspect all review threads, implement valid late feedback, reply with commit and validation evidence, request a fresh final-head review, and require successful CI/Security. Refresh threads immediately before merging. Do not close #281 while pending dispositions or actionable findings remain.

Protected merged PR #364 supplies 47 individually inspected dispositions, including six verified existing-code or explicitly accepted policy findings. Its documented mutable-review timing limitation remains an accepted policy decision.

Protected merged PR #397 fixes expired invitation replacement, retained deactivation reasons and the final active administrator concurrency invariant. Regressions cover current actor authorization and tenant-bound audit scope; its actual PostgreSQL CI passed 107 tests, including acceptance/replacement and cross-deactivation races.

Protected merged PR #394 fixes five individually reproduced manual review protocol findings and verifies fourteen related existing behaviors. Its final head passed independent review, all PR/push CI and Security, and the dedicated App gate before trusted merge.

Protected merged PR #396 fixes eleven individually audited workflow publication findings. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; the narrow temporary CI-selector approval was removed after trusted merge.

The closed #396 no-op edit review is also recorded as fixed with its strict canonical resolver evidence and protected merge receipt.

Protected merged PR #393 fixes the reproduced document finalization finding and four late storage/recovery findings, alongside 49 individually verified historical dispositions. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; the narrow temporary CI-selector approval was removed after trusted merge.

Protected merged PR #397 fixes four historical platform controls findings and three late administrator authorization, audit scope and acceptance race findings. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; the narrow temporary CI-selector approval was removed after trusted merge.

The biometric evidence audit individually reads seventeen historical findings. Six require fixes for malformed detection evidence, missing failure reasons and lost timeout classifications; eleven existing claim, ownership, fallback, promotion and finalization behaviors are independently verified on main. Invalid recovered results also receive contract validation before use. Actionable findings remain open until protected merge.

Protected merged PR #398 fixes eleven historical template lifecycle/forms findings and the late numeric version alias finding. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; the narrow temporary CI-selector approval was removed after trusted merge.

Protected merged PR #399 fixes six historical biometric evidence findings and the late stale success envelope finding. Its final head passed fresh review after canonical resolver evidence, all PR/push CI and Security and dedicated App validation. Required PostgreSQL CI passed migration and concurrency coverage; native protection was verified after trusted merge.

The public contract audit individually verifies seventeen historical authentication, route parity, reference, example and documentation findings against main. All 42 contract/backend tests and two actual Node 24 request-template cases passed, including four added boundary regressions; existing contract tests are preserved. No production-code change was needed.

Protected merges #400, #401 and #402 preserve release evidence, Paystack billing/recovery and workflow instantiation protections. Their final heads passed required review, CI, Security and dedicated App validation; narrow temporary CI-selector approvals were removed after merge. Eleven additional historical webhook and verification-result findings were individually checked against immutable main and passed 50 webhook and 21 result/reviewer/simulator PostgreSQL regressions.

Protected merged PR #403 verifies seventeen historical public contract findings, preserves prior contract tests and records the valid review correction: browser-facing mocks do not establish BFF integration coverage. Final-head review, PR/push CI, Security and the dedicated App gate passed before merge. Its regression suite passed 42 backend contract tests and two Node request-template tests.

Protected merged PR #405 fixes malformed BYOP signing headers and key-rotation replay claims, with ten signing and 210 broader common/provider regressions passing (five skips). Protected merged PR #404 fixes actual BFF path routing, bounded streamed bodies and browser integration coverage. Its final CI runs passed the standalone HTTP and real Chromium/WebKit BFF checks, final-head independent review, Security and dedicated App validation; its temporary workflow approval was removed. Subject network metadata and the remaining shared-store/signed-transport integration findings remain actionable until protected remediation merges.

On 2026-10-18, 45 additional historical comments were individually inspected against
immutable main `07a683f`: 23 existing-code findings were verified with 108 focused
baseline backend tests and the fresh frozen frontend install; 22 reproduced defects
remain actionable until protected remediation merges. The proposed frontend and
platform invitation/review fixes do not close the unordered active-liveness finding.

A second immutable-main inspection verified 21 additional existing implementations
and identified four additional actionable UI/documentation findings. Three baseline
suites now total 174 passing backend tests; no pending finding is classified by
thread resolution state alone. Reviewer RBAC, workflow creation steps and ordered
active liveness remain explicit engineering work after this batch.
