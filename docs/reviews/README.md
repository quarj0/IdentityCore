# Historical review audit (#281)

The disposition register tracks findings by original PR, comment and thread identifier. A resolved GitHub thread does not establish that its finding was implemented. Completed dispositions cite inspected implementation and regression evidence.

860 threads from closed or merged PRs: 237 fixed, 503 verified, 120 actionable and 0 pending individual audit. Actionable findings remain open until their remediation merges; resolution state is not implementation evidence. It extends the original 484-thread scope with subsequent closed-PR feedback. The original issue remains open.

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

Reviewer-permission remediation adds a mandatory `review_verification` boundary,
a narrowly scoped built-in-role migration and REST/GraphQL/service negative tests.
It remains actionable until protected review and merge; membership and queue skills
never substitute for the role grant. See [rollout](../operations/reviewer-permissions.md).

Workflow authoring remediation now submits an explicit supported step sequence,
provides a working draft editor, and rejects invalid creation payloads before
persistence. Backend tests cover create/publish/edit/republish with immutable prior
versions. Findings remain actionable until protected review and merge.

Active-liveness remediation replaces unordered action membership with exact ordered
observations, binds provider results to the issued challenge and protocol, and
bounds challenge issuance across replacement sessions. The motion approximation
and finite challenge space require physical/adversarial evaluation before production
claims; synthetic regressions establish the contract. The finding stays actionable
until protected review and merge.

Eight more original workflow comments were individually inspected. Two lineage/PDF
behaviors were verified against immutable main with two focused regressions; six
findings remain actionable. Their remediation restores onboarding state, clears clone
replay identity, loads lineage efficiently and repairs legacy names/JSON snapshots
without rewriting audit events or retained evidence artifacts.

Twelve additional portal/catalog/dependency findings were individually inspected.
Nine are superseded by current headers, consent-aware transfers, catalog fields,
ignored test state and the frozen shared dependency/browser matrix. Three reproduced
BFF session-isolation/exchange and development-CSP defects remain actionable; the
remediation includes actual two-tab BFF and retry journeys and keeps production CSP
strict. Two immutable-main catalog/consent-aware upload regressions passed.

Sixteen further original comments were individually inspected: five existing
origin, transfer-mock, request-timeout, bounded-input and tuple-typing fixes were
verified; eleven remain actionable. The portal batch also handles duplicate session
findings, public return build inputs, production-server test ownership and handoff
body deadlines. Remaining Arabic copy, private vulnerability reporting, issue forms
and backend dependency-group selection are confirmed work for subsequent batches.

Two original test-entrypoint findings were individually verified: common Django
tests were already selected and the frozen graph already uses one supported OpenCV
distribution. Fresh isolated setup passed model drift, 69 public OpenAPI operations,
1,234 backend tests (1,186 passed, 48 skipped), the OpenCV verifier and all 82 AI tests.
Dependency groups and AI working-directory selection are now explicit. Typed issue
forms and private-intake guidance are prepared, but GitHub returned HTTP 403 when the
integration attempted to enable private reporting; administrator activation remains
a release blocker. Findings remain actionable until protected review and merge.

Arabic remediation completes controlled journey/fallback copy and shared theme/skip
controls, preserves supplied organization/provider content, and makes legacy outcome
URLs use authenticated session state. English/Arabic browser journeys cover the
presentation boundary. The finding remains actionable until protected merge. Two
related originals were individually verified against immutable main: backend locale
quality weighting and render-error logging without arbitrary error messages.

A further 34 original comments were individually read against immutable main
`07a683f`: thirteen existing implementations are verified and twenty-one remaining
defects are actionable. Nineteen immutable-main auth/locale/cursor regressions and
six direct Node developer-origin/request-template tests passed. Verified behavior
includes scoped cursors, the traversal index, token registration/legacy rotation/
cleanup/logout failures, provider duration exposure and distinct capture attempts.
The remaining manifest integrity, historical detection evidence, isolation matrix,
credential environment, timing, frontend CSP/navigation and documentation gaps
remain engineering work. Creation-date validation/contract/SDK remediation now rejects impossible dates
and retains inclusive date filters through all four SDK pagination methods.
Typed JavaScript, Python, Java and .NET regressions/builds and contract/model
checks pass; live compatibility services were not configured. None of these
findings is closed before protected merge.

Setup/retention/navigation remediation now documents real-mode model provisioning
before stack startup, corrects the Compose mypy working-tree target, records actual
account-token retention and gives persisted notifications their own processing
activity. Security keeps the shared settings navigation. These five findings remain
actionable until protected merge; documentation does not claim automated retention
that the code does not implement.

Project environment remediation makes the public creation-time environment immutable
before credential issuance or verification activity, preventing sandbox secrets from
being promoted through a project edit. Ordinary partial settings updates preserve
omitted fields. One additional original unsupported-action review was individually
reproduced and remediated with the standard error envelope; both findings stay
actionable until protected merge. See [ADR 056](../decisions/ADR-056-immutable-project-environment.md).

Selfie evidence remediation records explicit correction provenance while clearing only
the pre-detection-migration default-one cohort without analysis attribution. Fresh
JSON/PDF exports include measured count/confidence/model attribution, unavailable
values and corrections. PDF pagination preserves late sections and long values.
Four dedicated regressions pass on SQLite and PostgreSQL, including populated legacy
migration; 83 broader regressions pass. The two findings remain actionable until
protected merge. The [maintenance guide](../operations/legacy-selfie-detection.md)
requires coordinated data migration rather than bypassing rollout checks.

A further eighteen originals were individually inspected: fifteen current-main
implementations are verified, with eleven immutable-main CORS/transition/session/
terminal-race regressions and two atomic PAD-fetch tests passing. Three remaining
findings track portal nonce forwarding, document completion chronology and missing
environment-denial audit events on retrieval. Two-capture timing remediation
preserves orchestrator timestamps; its prior-head regression reproduced three
backwards completion times without losing the four independent invocation records.
The audit remains open until all pending/actionable dispositions are completed.

Frontend CSP remediation forwards the portal's policy to its renderer and allows
configured dashboard image/upload origins without broadening script/inline-style
rules. Native onboarding progress replaces the blocked inline transform. Three
allowlist units, two production dashboard browser cases and four portal nonce/Arabic
journey cases pass across Chromium/WebKit. Exact script nonces, hydration, allowed
asset/PUT requests and blocked unlisted connections are verified. These four
findings stay actionable until protected merge; configuration is documented in the
[frontend guide](../../frontend/README.md#dashboard-csp-resource-configuration).


Sixteen upload/session originals were individually inspected against immutable main:
fourteen are already addressed, with 99 baseline upload/video/session tests passing.
Two transaction findings remain actionable. Their remediation moves multipart,
inspection and storage outside SQL and checks fresh purpose-bound consent before
acceptance. PostgreSQL barriers cover withdrawal during a write and two simultaneous
identical candidates; a losing request deletes only its own candidate. See
[ADR 057](../decisions/ADR-057-upload-transfer-transactions.md) for admission,
receipt and uncertain-commit cleanup limits.


Model-integrity remediation separately pins the reviewed manifest digest in trusted
deployment configuration, mounts inference assets read-only and rejects unlisted or
omitted configured models and runtime downloads. Streamed startup hashing and a
metadata-invalidated cache avoid per-request full-volume reads. Alias-safe bootstrap
and real-processing denial regressions are included; all 91 AI tests pass. These
four findings remain actionable until protected merge. The
[provisioning guide](../operations/ai-models.md) requires independent release approval,
no concurrent writers and worker restart; synthetic tests do not certify real models.


Environment-denial remediation audits same-tenant wrong-environment retrievals and
rejected actions after mutation rollback. Three transaction-level regressions cover
policy and eight verification routes, full error equivalence, chain integrity and
absence of false events for foreign/unknown/success/list requests; 60 focused tests
pass. IC-011/#95 and the historical finding stay open until protected merge.


Thirty additional originals were individually read: fifteen existing decision-contract,
maker/checker, upload, UI approval, authorization, throttle and Node compatibility
implementations are verified against immutable main; 202 contract/review/auth/session
baseline tests pass alongside the prior 99 upload/video/session checks. Fifteen actual
gaps remain actionable: six privacy deletion findings, audit verification, hold
ownership, three seed issues, three security-report/gate findings and backlog parsing.
Operator verification, hold/seed invariants and strict parsing are prepared in the
operational follow-up. Their prepared remediations follow below; the remaining audit and protected
review/merge remain open.


The operational follow-up passes 25 focused checks, 41 document/retention recovery
checks, strict valid/malformed backlog parsing and the full backend suite: 1,252 run,
1,203 passed and 49 skipped. The two-capture timing scenario now has its own test,
preserving single-capture recovery fixtures and all invocation chronology assertions.
No pending disposition or unmerged remediation is represented as completed.


Security workflow remediation retains unfixed findings in JSON artifacts and runs
dependency/secret enforcement independently unless cancelled. These three findings
remain actionable, with governed protected-definition review and approval required
before merge. This does not resolve the current secret alert or claim deployed scans.


Subject privacy boundary remediation requires a narrowly granted privacy permission,
revokes sessions/jobs, cancels unfinished cases and scrubs copied verification
references, provider results and prior subject exports. Report pointers stay tracked.
The current-actor and cached-export safeguards, migration grant boundaries and two
PostgreSQL finalization races are covered alongside existing fingerprint races.
All six privacy findings are prepared, not closed; notification and report
remediations are included in the subsequent batches below. All remain open until protected merge; see the
[privacy procedure](../operations/subject-privacy.md).


Notification privacy remediation binds new applicant messages to their subject,
scrubs linked/current-contact legacy matches and prevents stale queue/result writes
from restoring personal data. Sent facts remain pseudonymous; unrelated recipients
and other bound subjects are preserved. Short transactions surround provider I/O;
already-admitted external sends cannot be recalled. Unknown historical ownership
requires controlled reconciliation. The finding remains actionable until merge.


Report retirement now preserves scoped JSON/PDF references through anonymization,
partial writes, route changes and failed deletion. Indexed deadline/attempt/completion
state prevents finished/failed cases from blocking later cleanup. Expired or retired
reports cannot be recreated by ordinary API access. Key outages leave deadlines
unset without blocking revocation; bounded repair retries after recovery. Full backend:
1,276 run, 1,223 passed, 53 skipped; 42 focused consent/retention and 14 PostgreSQL
checks pass, including populated migration and storage-outside-SQL checks. The finding
remains actionable until protected merge. Legacy references and uncertain/crashed
external writes require [controlled reconciliation](../operations/evidence-report-retention.md).

Twenty-five more original comments were read and compared with immutable main:
eighteen existing behaviors are verified and seven gaps remain actionable. Baseline
validation includes 154 backend checks (153 passed, one skipped), six direct Node
API-origin/request-template checks and 16 unchanged CLI checks (15 passed, one skipped).
The prepared upload changes admit legacy completion through the narrow BFF and
journal original-object deletion, preserving references through outstanding grant
expiry, retries and holds. A populated migration and actual PostgreSQL transaction
checks cover the cleanup path. This does not close the finding before protected merge;
see the [upload procedure](../operations/upload-transfers.md).

Upload cleanup validation: full backend 1,281 run, 1,228 passed, 53 skipped;
five focused cleanup tests and nine actual PostgreSQL cleanup/transfer checks pass.
The production portal build (webpack) and standalone BFF's 19 HTTP plus 20
Chromium/WebKit browser checks pass. Turbopack hit the execution sandbox's port-binding
restriction; the successful webpack build is the production artifact tested here.
The processing inventory covers all 1,174 persisted fields and its seven checks pass.


Prepared review/lifecycle follow-ups dispatch direct failed outcomes, expose current
checker eligibility and show an independent waiting state, repair missing legacy
cancellation timestamps without duplicating cancellation side effects, and preserve
a displayed signing secret when endpoint creation fails. Dashboard self-origin
configuration now documents its production build-time requirement. These findings
remain actionable until protected merge.

A further twenty original recovery/accessibility comments were individually read:
eight existing changes are verified by source inspection and twelve are actionable.
These include document terminal/route-exhaustion recovery and gaps in mounted-state,
keyboard, handoff, evidence and nonce-compatible accessibility coverage. Existing
mobile coverage does not establish that every mounted capture state is scanned.
No accessibility certification or finding closure is inferred from test names.

The recovery audit's unchanged immutable-main storage/document/notification baseline
passes all 29 checks. Accessibility findings above remain source-confirmed gaps,
with no claim that their failing browser paths have yet been repaired.

Fifteen further originals were inspected individually: thirteen existing logging and
incident-response behaviors are verified, with ten immutable-main direct Node
redaction tests and fourteen scanner tests passing. Two additional accessibility
coverage gaps remain actionable: waiting for the actual handoff DOM before scanning
and exercising verified/failed terminal panels. Deployed hold/replay procedures and
incident drills still require operator validation.

Review/lifecycle validation: full backend 1,285 run, 1,232 passed, 53 skipped; 32
GraphQL/protocol checks pass after including the approval hint in the GraphQL node.
Nine focused transition/review checks and 19 queue/reason checks (one skipped) pass.
Production dashboard build and six Chromium/WebKit regressions cover both approval
states and failed-create secret preservation. Types, changed-source lint, all 69
OpenAPI operations and SDK model drift checks pass. An initial GraphQL incompatibility
was corrected before these successful checks; no security or access gate was weakened.

Fifteen more original platform/API comments are verified against immutable-main
source, with nine direct API-client and 68 analytics/organization/webhook checks
passing. This includes existing retry/cancellation safeguards, replay provisioning,
aggregate consistency and per-draft branding keys. Actual storage signature enforcement
and browser accessibility are not inferred from those source checks.

Prepared document recovery recognizes exact resource-bound route exhaustion before
redispatch, reconciles unfinished documents at the attempt limit and rejects stale
owners. Already-terminal cases stop new provider work; cancellation during an admitted
failure preserves the owned failure and terminal case outcome. An existing success-race
test now triggers cancellation during its provider callback, preserving its original
processed-document assertions; separate tests cover cancellation before processing.

Document recovery validation passes 21 focused document/job checks, nine actual
PostgreSQL recovery/consent checks and the full backend: 1,290 run, 1,237 passed,
53 skipped. Prepared recovery findings remain actionable until protected merge.

Twenty provider/evidence originals were individually verified against immutable main,
including compatible manifest activation locks, risk runtime, policy clone controls,
backup reference selection, telemetry, MRZ/date boundaries and bounded evaluation.
Baseline: 70 backend checks (68 passed, two PostgreSQL-only skipped), 12 MRZ parser
and ten locked-evaluation checks passed. This does not certify external providers,
real model accuracy or a deployed restore drill.

The last twenty original comments were individually verified against immutable main:
87 backend checks (81 passed, six PostgreSQL-only skipped) and seven deployed-security
script checks passed. These cover handoff/provenance, fingerprint erasure/draining,
security checks, rollout guards, refresh credentials and tenant-key/storage invariants.
Every original now has an individual disposition. The audit issue remains open:
actionable fixes still require implementation where noted, independent review and
protected merge. Real deployment, restore and device/model validation is separate.

Prepared accessibility remediation consolidates the duplicate applicant journey into
English/Arabic keyboard and touch scenarios across four browser profiles. It scans
captured images, mounted camera/recording/review states, QR waiting/copy and separate
verified/failed panels, and exercises reviewer supporting evidence. Shared axe includes
WCAG 2.1 A and uses the response nonce with CSP enforced. Scans exposed and corrected
preview/ready-caption contrast and a nested QR image lacking alternate text.

Production applicant checks passed 18 cases with two intentional mobile initiating-QR
skips. The broad admin run passed 30 cases; its two WebKit timeout cases passed on a
quiet rerun, preserving all assertions. The focused reviewer scenario also passed both
browsers. Types/lint and production builds pass. These eleven findings stay actionable
until protected merge; physical-device and assistive-technology assurance is separate.
See [accessibility validation](../operations/accessibility-validation.md).

Python SDK support now starts at 3.12, matching the backend minimum. Compatibility CI
targets 3.12 and 3.14 instead of the unsupported Ubuntu 26.04/Python 3.9 combination.
The changed CI definition still requires governed review/approval. A PostgreSQL-only
review-race fixture now receives the explicit reviewer permission; authorization and
all conflict assertions remain enforced. Its five PostgreSQL checks pass.

Both Python 3.12 and 3.14 pass the SDK unit and actual local HTTP compatibility
checks against an isolated Django fixture (28 run, one unrelated skip per runtime).
The newer runtime exposed an unclosed HTTP error response; the transport now closes
error responses after reading them, preserving the API error behavior.

Prepared tenant-isolation coverage now checks object mutations/actions across the
tenant dashboard, including invitations, policies, reviews, provider configuration,
consent, KMS and billing. Foreign and unknown identifiers must return identical
complete error envelopes except for request IDs, while foreign fields and resource
counts remain unchanged. Legitimate permissions and required idempotency headers are
provided; applicant-token and platform-only authorization remain separate suites.
The complete PostgreSQL CI selection now passes all 235 checks after correcting the
reviewer fixture. Historical dispositions remain actionable until protected merge.

Final combined backend validation ran 1,291 tests: 1,238 passed and 53 skipped.
The PostgreSQL CI selection separately passed all 235 checks; the final focused
tenant-isolation matrix also passed with persisted-field and resource-count checks.

The immediate work is consolidated for review in existing PR
[#433](https://github.com/quarj0/IdentityCore/pull/433), preserving the commits and
original conversations from #406–#432. Superseded drafts are not separate merge
candidates. Closing them does not resolve findings or mark prepared work as merged.
Final-head independent review, CI/Security, dedicated App evidence and protected
workflow approval remain required. The current integration cannot read native
branch protection (HTTP 403); no trusted merge has been performed.

The reproduced portal container failure came from production TypeScript compilation
including browser tests that import a platform-admin module absent from the image.
Application builds now exclude browser fixtures; the explicit CI typecheck runs both
application and browser-test configs. Both checks pass. The complete Alpine image
build also passes using a temporary local proxy/CA adapter, and its unprivileged
runtime (UID 1001) serves `/api/health` with HTTP 200. No TLS verification or TypeScript
checks were disabled. The Dockerfile ignore file keeps host dependencies, environment
files and build/test artifacts outside the image build context.

Follow-up on the consolidated PR's native checks: the withdrawal allowlist browser
fixture still used obsolete shared cookies and omitted the session ID header. It
now uses the session-scoped cookie/header contract; the four browser profiles pass.
The review bot's creation-date index finding is addressed with timezone-aware
start/end timestamp bounds on the raw column, with inclusive DST boundary coverage.
Three date-filter regressions pass. The API specification documents those bounds.

A separate PostgreSQL run with CI's actual base settings reproduced two failures
hidden by the testing settings' configured invitation URL. The historical admin
fixture now explicitly supplies a safe HTTPS delivery URL; production URL validation
is unchanged. The earlier 235-test result used testing settings and does not by
itself establish a passing base-settings CI run.

AI dependency installation was reproduced with Python 3.14: pinned PaddlePaddle
3.3.1 has wheels for CPython 3.12/3.13 and cannot install on 3.14. Frozen Python
3.12 dependency selection succeeds and all 91 local AI tests pass. An exact
three-line proposal selects Python 3.12 for backend/migration/AI CI while retaining
SDK 3.14 coverage. The protected workflow was not changed: automatic approval review
rejected the edit because narrow publisher-environment approval is absent. Final
head review and governed publisher approval remain required before merge.

The consolidated review also identified a creation/subject-erasure race. The common
REST/GraphQL creation serializer now holds the tenant audit lock before finding a
subject or inserting a case/session, and reuses only a locked live subject. Two
PostgreSQL regressions failed against the previous code and pass with this change,
checking actual database lock waits and both transaction orderings. Creation first
is captured by deletion; deletion first causes a fresh profile rather than reuse
of the erased profile. The session authentication fail-closed check is preserved.
The 235-check CI selection with base settings passed after fixing the HTTPS fixture;
the final run additionally includes both existing and new privacy race modules.

Final combined backend validation after these follow-ups ran 1,294 tests: 1,239
passed and 55 skipped; PostgreSQL coverage is validated separately. The date-filter regressions also pass
on PostgreSQL with CI base settings. GitGuardian still reports incident 38304031
for the deterministic signing test vector in `docs/fixtures/provider-signing-wire-v1.json`.
Python/JavaScript conformance derives that value from the checked-in synthetic
fixture credential; the external scanner disposition remains pending. No alert was
dismissed and no scan exclusion was added.

The final PostgreSQL run passed all 239 checks with CI base settings, including
the existing deletion/finalization races and the two new creation/erasure races.
The proposed CI patch includes these privacy modules explicitly; it remains
unapplied while approval is pending. Final type, formatting, Ruff and diff checks pass.
