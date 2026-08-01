# IdentityCore Implementation Backlog

Last reviewed: 2026-08-01

This is the ordered, issue-ready backlog for moving IdentityCore from its current
working vertical slice to a production-capable identity infrastructure platform. Each
row is intentionally small enough to become one GitHub issue. IDs are stable so issues,
pull requests, and architecture decisions can refer to them before GitHub issue numbers
exist.

## How to use this backlog

1. Work in milestone order. Within a milestone, take `P0` before `P1`, then `P2`.
2. Confirm every listed dependency is complete before assigning an issue.
3. Copy the row's outcome and acceptance checks into the matching GitHub issue form.
4. Keep one issue focused on one independently reviewable outcome; split it if its pull
   request grows across unrelated subsystems.
5. Close an issue only when its acceptance checks, automated tests, documentation, and
   security/privacy review (where applicable) are complete.

The `Sync implementation backlog issues` GitHub Actions workflow creates these as real
GitHub issues when this file reaches `main`. It can also be run manually. Synchronization
is idempotent: the stable ID marker updates an existing generated issue rather than
creating a duplicate. To preview locally, run:

```bash
python scripts/sync_github_issues.py
```

Suggested labels are `type:bug`, `type:feature`, `type:security`, `type:test`,
`type:docs`, `area:backend`, `area:ai`, `area:frontend`, `area:platform`, `area:sdk`,
and priorities `P0` through `P2`.

## Milestone 0 — Baseline and developer reliability

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-001 | P0 | bug | Make a clean checkout reproducibly install all frontend workspaces from the root lockfile. | Frozen install succeeds; app-local lockfile policy is documented; CI uses the same command. | — |
| IC-002 | P0 | test | Add one root command that runs backend, AI, frontend, and SDK test suites. | Command fails on any child failure; output identifies the failing suite; README documents it. | IC-001 |
| IC-003 | P0 | bug | Remove tracked runtime artifacts such as SQLite databases, static build output, and test results. | Artifacts are untracked; ignore rules cover regeneration; tests create data in temporary paths. | — |
| IC-004 | P0 | feature | Add startup configuration validation for required secrets and unsafe production defaults. | Production startup rejects missing/placeholder secrets; local development remains documented and usable; tests cover both modes. | — |
| IC-005 | P1 | test | Add migration-drift and missing-migration checks to CI. | CI detects model changes without migrations and verifies all migrations apply to an empty PostgreSQL database. | IC-002 |
| IC-006 | P1 | feature | Publish a local seed command with deterministic tenants, users, policies, and verification cases. | Command is idempotent; generated credentials are development-only; all major UI states have fixtures. | IC-004 |
| IC-007 | P1 | docs | Replace stale scaffold READMEs with app-specific setup, commands, ports, and environment variables. | Every runnable service has copy/paste setup and test instructions; links resolve. | IC-002 |
| IC-008 | P1 | test | Add dependency, secret, and container vulnerability scanning to CI. | Findings are uploaded as artifacts; severity policy is documented; high/critical findings fail protected builds. | IC-002 |

## Milestone 1 — Tenant isolation and authentication hardening

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-009 | P0 | security | Build a tenant-isolation test matrix for every tenant-owned REST resource. | Cross-tenant read/write/list/delete attempts return non-disclosing failures; matrix runs in CI. | IC-005 |
| IC-010 | P0 | security | Apply the same tenant-isolation matrix to internal GraphQL queries and mutations. | Node lookup, filters, mutations, and nested relationships cannot cross tenant boundaries; tests run in CI. | IC-009 |
| IC-011 | P0 | security | Enforce environment scope on API clients, policies, sessions, providers, and webhook endpoints. | Sandbox credentials cannot access production objects and vice versa; attempts are audited; regression tests exist. | IC-009 |
| IC-012 | P0 | security | Implement short-lived access tokens with refresh-token rotation and reuse detection. | Refresh tokens rotate atomically; replay revokes the token family; logout invalidates the session; tests cover races. | IC-004 |
| IC-013 | P0 | security | Require MFA for platform administrators and configurable privileged organization roles. | Enrollment, recovery codes, challenge, reset, and audit events work; bypass paths are tested. | IC-012 |
| IC-014 | P0 | security | Complete API-key rotation with overlap windows and last-used metadata. | New key is shown once; old key expires after the configured window; hashes only are stored; every action is audited. | IC-011 |
| IC-015 | P1 | feature | Add organization invitation, expiration, resend, acceptance, and revocation flows. | Single-use expiring invitations enforce role and tenant; existing-account and new-account paths are tested. | IC-012 |
| IC-016 | P1 | security | Centralize object-level authorization in explicit permission policies. | REST, GraphQL, tasks, and service calls use the same policy decisions; deny-by-default tests cover every role. | IC-009, IC-010 |
| IC-017 | P1 | security | Add session/device management for dashboard users. | Users can inspect and revoke sessions; sensitive account changes revoke other sessions; IP/user-agent display is privacy-safe. | IC-012 |
| IC-018 | P1 | bug | Prevent user and organization enumeration in login, password reset, invitations, and public session lookup. | Equivalent responses and rate limits are verified by tests; logs retain actionable internal reasons without exposing them. | IC-012 |

## Milestone 2 — Verification workflow correctness

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-019 | P0 | bug | Make verification state transitions atomic and reject invalid or repeated transitions. | A documented transition table is enforced under concurrency; duplicate requests are idempotent; audit order is stable. | IC-005 |
| IC-020 | P0 | security | Bind subject session tokens to one verification, expiry, and allowed action set. | Tokens cannot be reused across sessions or after completion/revocation; token material is never logged; tests cover tampering. | IC-019 |
| IC-021 | P0 | feature | Persist immutable policy and workflow snapshots for every verification. | Later configuration edits do not change an in-flight decision; snapshot version appears in evidence and audit output. | IC-019 |
| IC-022 | P0 | bug | Make evidence upload completion idempotent and safe under duplicate callbacks. | Duplicate complete calls create one evidence record and one processing chain; checksum/size/type are revalidated server-side. | IC-019 |
| IC-023 | P0 | feature | Add cancellation, expiration, and abandonment handling for verification sessions. | Scheduled expiry is deterministic; terminal states reject uploads; webhook and audit events are emitted once. | IC-019 |
| IC-024 | P0 | security | Add malware scanning and content-sniffing quarantine before document processing. | Claimed and detected types must match policy; infected/unknown files never reach processors; safe failures route correctly. | IC-022 |
| IC-025 | P1 | feature | Support required front/back document evidence and pair consistency. | Workflow declares required sides; duplicates/missing sides are rejected; reviewers see the linked pair. | IC-021, IC-022 |
| IC-026 | P1 | feature | Add resumable mobile handoff with one-time QR/deep-link claims. | Handoff is short-lived and single-use; desktop status updates without token leakage; cross-session claims fail. | IC-020 |
| IC-027 | P1 | bug | Recover processing jobs stuck by worker loss or deployment. | Leases/heartbeats identify stale work; retries are bounded and idempotent; terminal exhaustion routes to review or failure. | IC-019 |
| IC-028 | P1 | feature | Return a stable, versioned verification result schema with evidence lineage. | Result includes decision, reasons, policy version, check provenance, and timestamps without internal IDs or sensitive raw payloads. | IC-021 |

## Milestone 3 — Provider-neutral execution (BYOP)

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-029 | P0 | feature | Define a versioned capability adapter interface and normalized result/error contract. | OCR, quality, classification, liveness, and face-match fixtures validate against one contract; an ADR documents versioning. | IC-028 |
| IC-030 | P0 | feature | Wrap the built-in AI service as adapters instead of calling it directly from tasks. | All five capabilities execute through the adapter registry; existing behavior and evidence attribution remain tested. | IC-029 |
| IC-031 | P0 | feature | Add an orchestration service that resolves, invokes, normalizes, and records a provider attempt. | Tasks use one service; timeouts/errors become normalized outcomes; every attempt has duration, provider, and redacted metadata. | IC-030 |
| IC-032 | P0 | security | Implement a secure custom HTTP adapter with destination allowlisting. | SSRF controls block private/metadata networks and redirects; TLS, timeout, body-size, and content-type policies are enforced. | IC-029 |
| IC-033 | P0 | security | Sign provider requests and verify timestamped, nonce-bound provider responses. | Replay and stale responses fail; keys can rotate; canonicalization has published cross-language fixtures. | IC-032 |
| IC-034 | P1 | feature | Model versioned environment-scoped provider routes and ordered fallback chains. | Routes support capability, country, document, and workflow conditions; deterministic precedence is tested. | IC-031 |
| IC-035 | P1 | feature | Add per-route timeouts, bounded retries, circuit breakers, and final actions. | Retryable errors are explicit; attempt history explains each fallback; open circuits recover safely; manual fallback is supported. | IC-034 |
| IC-036 | P1 | feature | Build organization provider setup, credential entry, connection testing, and assignment UI. | Secrets never return to the browser; permissions and environment scope are enforced; test outcomes are audited. | IC-032, IC-034 |
| IC-037 | P1 | feature | Add provider health, latency, error-rate, and availability views using redacted telemetry. | Metrics are tenant/environment scoped; payloads and PII are absent; route health can be inspected without secret access. | IC-031 |
| IC-038 | P1 | test | Publish provider conformance fixtures and a contract test runner. | A provider can validate success, malformed, timeout, replay, and version-negotiation cases locally; CI tests built-in adapters. | IC-033 |
| IC-039 | P2 | feature | Define provider capability manifests with coverage, residency, retention, and schema metadata. | Manifests are versioned and validated; incompatible assignments are rejected before activation. | IC-029 |
| IC-040 | P2 | feature | Add sandbox-to-production provider configuration promotion with approval. | Promotion produces a diff; secrets are separately supplied; privileged approval and fresh connection tests are required. | IC-036, IC-039 |

## Milestone 4 — Document, biometric, and fraud evidence

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-041 | P0 | bug | Replace placeholder document face counts with AI-produced, versioned evidence. | Zero/multiple faces route per policy; model/version/confidence are persisted; unavailable analysis never silently passes. | IC-030 |
| IC-042 | P0 | bug | Replace placeholder liveness and face-match lifecycles with real asynchronous results. | Checks reach terminal states exactly once; scores and thresholds are traceable; unavailable/inconclusive results route to review. | IC-031 |
| IC-043 | P0 | security | Validate model assets by checksum and fail closed in production real-inference mode. | Startup/readiness identifies missing or altered assets; mock fallback cannot activate in production; runbook covers recovery. | IC-004 |
| IC-044 | P1 | feature | Implement MRZ parsing and check-digit validation for supported documents. | Valid and invalid ICAO fixtures are covered; normalized fields retain provenance; unsupported formats are explicit. | IC-029 |
| IC-045 | P1 | feature | Add document expiry, issue-date, age, and cross-field consistency signals. | Country-aware rules are versioned; clock boundaries are tested; signals inform policy rather than hard-coded decisions. | IC-044 |
| IC-046 | P1 | feature | Add duplicate and velocity signals for document, portrait, device, and network reuse. | Tenant/global scope is policy-controlled; identifiers are privacy-preserving; thresholds and retention are configurable. | IC-021 |
| IC-047 | P1 | security | Add capture provenance and replay/media-injection defenses to the verification portal. | Capture metadata is signed; known replay paths are rejected or flagged; unsupported browsers get a safe fallback. | IC-026 |
| IC-048 | P1 | feature | Make document authenticity a first-class provider capability and evidence type. | Taxonomy, adapter schema, routing, policy consumption, UI, and audit lineage are implemented end to end. | IC-034 |
| IC-049 | P2 | feature | Add explainable suspicious-region annotations for document tampering signals. | Reviewers see bounded overlays and reasons; coordinates survive image transforms; raw model output remains versioned. | IC-048 |
| IC-050 | P2 | test | Create locked evaluation harnesses for liveness, face match, OCR, and authenticity. | Reports include dataset/model versions, precision/recall and error rates; thresholds are reproducible; no test biometric data is committed. | IC-043, IC-048 |

## Milestone 5 — Decisions and manual review

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-051 | P0 | feature | Version the decision engine contract and persist every input and reason code. | A decision is reproducible from its snapshot; missing/unknown evidence fails safely; output uses stable public reason codes. | IC-021, IC-028 |
| IC-052 | P0 | security | Enforce reviewer assignment, tenant scope, and least-privilege evidence access. | Unassigned/unauthorized access fails; assignment races are atomic; sensitive views produce audit events. | IC-016 |
| IC-053 | P0 | feature | Add maker-checker approval for high-risk or policy-selected review outcomes. | One actor cannot perform both steps; escalation and rejection are supported; finalization is atomic and audited. | IC-052 |
| IC-054 | P1 | feature | Add review queues with priority, SLA, skill/country filters, and fair assignment. | Deterministic queue rules avoid double assignment; overdue cases are visible; configuration is tenant scoped. | IC-052 |
| IC-055 | P1 | feature | Add structured reviewer reason codes and mandatory notes by outcome. | Policies configure required fields; unsafe HTML is rejected; result payload exposes only approved organization-facing reasons. | IC-051 |
| IC-056 | P1 | bug | Prevent a late automated result from overwriting a human or terminal decision. | Optimistic locking rejects stale writes; race tests cover task/reviewer completion; conflicts are audited. | IC-019, IC-053 |
| IC-057 | P1 | feature | Add review quality sampling and second-review disagreement reporting. | Sampling rules are configurable; reviewers cannot inspect their own QA assignment; reports avoid unnecessary biometric exposure. | IC-053 |
| IC-058 | P2 | feature | Add a versioned external risk-engine capability through provider orchestration. | Minimal normalized inputs are sent; output maps to evidence, not direct approval; timeout/fallback behavior is policy controlled. | IC-035, IC-051 |

## Milestone 6 — Privacy, audit, and data lifecycle

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-059 | P0 | security | Make audit events append-only and tamper-evident. | Application roles cannot update/delete events; hash-chain or equivalent integrity verification is tested; export verification is documented. | IC-005 |
| IC-060 | P0 | security | Implement evidence retention policies and verified deletion jobs. | Retention is purpose/environment scoped; storage and database deletion are idempotent; legal holds prevent deletion; outcomes are audited. | IC-023 |
| IC-061 | P0 | feature | Add data-subject export with authorization, redaction, and expiring delivery. | Export covers documented personal data; secrets/internal notes are excluded; generation and download are audited. | IC-060 |
| IC-062 | P0 | feature | Add data-subject deletion/anonymization workflows with legal-hold handling. | Dependencies are documented; required audit facts remain pseudonymized; completion report lists retained categories and reasons. | IC-060 |
| IC-063 | P1 | security | Introduce per-tenant, per-environment envelope-encryption key versions. | New writes use active keys; reads support old versions; rotation is resumable; plaintext/key material never enters logs. | IC-004 |
| IC-064 | P1 | feature | Add customer-managed KMS/HSM key provider integration. | Connection validation, grants, rotation, disablement, outage behavior, and audit trail are covered by contract tests. | IC-039, IC-063 |
| IC-065 | P1 | feature | Add tenant-routed object storage with reference-only evidence transfer. | Bucket/prefix isolation is enforced; signed grants are minimal and expiring; deletion and residency metadata follow the object. | IC-034, IC-060 |
| IC-066 | P1 | security | Create centralized structured-log redaction for secrets, tokens, PII, and biometric payloads. | Known sensitive field corpus is tested across Django, Celery, AI, and frontend logging; unsafe payload logging fails lint/tests. | IC-008 |
| IC-067 | P1 | feature | Record and enforce consent purpose, version, locale, withdrawal, and evidence scope. | Processing checks active purpose-bound consent; withdrawal blocks future processing; immutable proof remains auditable. | IC-021, IC-060 |
| IC-068 | P2 | docs | Build a records-of-processing and data-flow inventory linked to services and providers. | Every sensitive field has purpose, location, retention, processors, and transfer notes; CI checks referenced owners/paths exist. | IC-039, IC-060 |

## Milestone 7 — API, webhooks, SDKs, and developer experience

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-069 | P0 | bug | Make the OpenAPI document match implemented public endpoints and schemas. | Automated schema diff/check runs in CI; examples validate; undocumented public routes and stale documented routes fail the check. | IC-028 |
| IC-070 | P0 | feature | Enforce idempotency keys on public create and retry-sensitive endpoints. | Same key/body returns the original response; mismatched bodies conflict; tenant scope, expiry, and concurrent requests are tested. | IC-019 |
| IC-071 | P0 | security | Version webhook payloads and signatures with replay-resistant verification. | Timestamp tolerance, event ID, secret rotation, and canonical fixtures work across supported SDKs. | IC-033 |
| IC-072 | P0 | bug | Guarantee webhook outbox consistency with domain transactions. | Committed events are eventually delivered; rolled-back events never deliver; duplicate delivery retains one stable event ID. | IC-019 |
| IC-073 | P1 | feature | Add webhook endpoint testing, disablement, replay, and dead-letter recovery. | RBAC applies; test events are unmistakable; replay is audited; repeated failures safely disable or alert per policy. | IC-071, IC-072 |
| IC-074 | P1 | feature | Add cursor pagination and stable filtering conventions across public list APIs. | Concurrent inserts do not duplicate/skip traversal; limits are bounded; SDK helpers iterate pages consistently. | IC-069 |
| IC-075 | P1 | feature | Generate typed SDK models from the validated OpenAPI contract. | Python, JavaScript, Java, and .NET compile/test against common fixtures; hand-written auth/retry layers remain documented. | IC-069 |
| IC-076 | P1 | test | Add SDK compatibility tests against a live disposable backend. | Supported language versions run create/get/list/error/webhook verification scenarios in CI. | IC-070, IC-071, IC-075 |
| IC-077 | P1 | feature | Build a deterministic sandbox simulator for approved, declined, review, timeout, and provider-error outcomes. | Scenarios are selected without production-only backdoors; events/results match production schemas; docs include examples. | IC-028, IC-071 |
| IC-078 | P2 | feature | Add API usage quotas and organization-visible rate-limit telemetry. | Limits are atomic and environment scoped; response headers are documented; dashboard shows usage without exposing other tenants. | IC-011, IC-074 |

## Milestone 8 — Frontend completeness and accessibility

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-079 | P0 | bug | Replace dashboard and platform-admin mock/sample data with authenticated APIs. | Empty/loading/error/permission states are real; no production build imports fixture data; API contracts are tested. | IC-069 |
| IC-080 | P0 | security | Apply a strict CSP and remove unsafe script/style requirements from all web apps. | Production headers pass an automated check; nonces/hashes cover required assets; violation reporting excludes sensitive URLs/data. | IC-004 |
| IC-081 | P0 | test | Run automated keyboard and WCAG accessibility checks on critical verification and review journeys. | Consent, upload, camera, handoff, review, and decision paths are keyboard operable; critical automated violations fail CI. | IC-002 |
| IC-082 | P1 | bug | Make verification capture recover predictably from camera denial, interruption, and unsupported devices. | Clear fallbacks preserve completed steps; retry does not duplicate evidence; browser/device matrix is documented. | IC-022 |
| IC-083 | P1 | feature | Add localization infrastructure and ship the applicant journey in at least two configured locales. | Locale negotiation/selection works; consent version records locale; dates, numbers, RTL readiness, and fallback are tested. | IC-067 |
| IC-084 | P1 | feature | Add tenant branding with safe asset upload and accessible color validation. | Environment preview/publish works; SVG/script hazards are blocked; contrast checks warn/block invalid critical combinations. | IC-024 |
| IC-085 | P1 | bug | Standardize frontend API errors, correlation IDs, retries, and expired-session behavior. | Errors never leak raw server details; safe retry is limited to idempotent operations; support IDs connect to backend telemetry. | IC-070 |
| IC-086 | P1 | test | Add Playwright coverage for organization setup through delivered verification result. | Tests cover happy, review, failure, mobile handoff, and webhook-visible states using deterministic fixtures. | IC-006, IC-077, IC-079 |

## Milestone 9 — Operations and pilot readiness

| ID | Pri | Type | Issue-ready outcome | Acceptance checks | Depends on |
| --- | --- | --- | --- | --- | --- |
| IC-087 | P0 | feature | Add service-level metrics, traces, and correlation across API, workers, AI, storage, and providers. | One verification can be traced end to end; labels avoid tenant/subject cardinality and PII; dashboards cover core SLIs. | IC-066 |
| IC-088 | P0 | feature | Define SLOs and actionable alerts for verification, queues, providers, webhooks, and storage. | Alerts map to runbooks; burn-rate thresholds are tested; planned maintenance and sandbox noise are handled. | IC-037, IC-087 |
| IC-089 | P0 | security | Implement encrypted automated backups and prove restore in an isolated environment. | RPO/RTO are documented; restore drill validates database/object consistency and tenant access; results are retained. | IC-060 |
| IC-090 | P0 | docs | Publish incident response, breach triage, evidence preservation, and notification runbooks. | Roles, severity, contacts, decision logs, exercises, and post-incident actions are defined; no secrets are committed. | IC-087 |
| IC-091 | P0 | test | Run production-like load tests for session creation, uploads, processing, review, and webhooks. | Capacity limits and bottlenecks are recorded; tests use synthetic data; pass/fail thresholds protect the pilot target. | IC-086, IC-087 |
| IC-092 | P1 | test | Add failure-injection tests for Redis, database, storage, AI, and provider outages. | Recovery avoids data loss/double decisions; degraded states are observable; each failure maps to a runbook. | IC-027, IC-035, IC-087 |
| IC-093 | P1 | security | Automate TLS, security-header, cookie, CORS, and public-endpoint deployment checks. | Checks run against a deployed environment; unsafe configuration blocks promotion; approved origins are environment scoped. | IC-080 |
| IC-094 | P1 | feature | Add zero-downtime migration and deployment health gates. | Backward-compatible rollout sequence is documented/tested; readiness drains workers; rollback does not corrupt in-flight work. | IC-027, IC-089 |
| IC-095 | P1 | feature | Build pilot onboarding and go-live readiness checklists per organization/environment. | Owners verify security, retention, consent, providers, limits, contacts, and rollback; approval is timestamped and auditable. | IC-088, IC-090 |
| IC-096 | P1 | feature | Add privacy-safe product metrics for completion, abandonment, review, latency, and failure reasons. | Metrics have documented definitions; tenant access is isolated; small-cohort/PII leakage is prevented; opt-out/retention are defined. | IC-067, IC-087 |

## Definition of done for every issue

- Acceptance checks are covered by automated tests where practical.
- Tenant and environment isolation are explicitly considered.
- Logs, metrics, errors, and audit events contain no unnecessary secrets, PII, document
  images, or biometric data.
- Public identifiers and versioned contracts are used at integration boundaries.
- Relevant OpenAPI, architecture, operations, and user documentation is updated.
- Migrations and background work are safe to retry and deploy incrementally.
- Security-sensitive changes include abuse cases and deny/failure-path tests.
- The pull request links the stable backlog ID and records the commands used to verify
  the change.
