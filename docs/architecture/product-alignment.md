# Product Alignment and Gap Assessment

Last reviewed: 2026-10-18

IdentityCore is a vendor-neutral identity infrastructure platform with a working
identity verification workload. Repository implementation, historical review closure,
and deployment assurance are separate milestones. The live
[issue tracker](https://github.com/quarj0/IdentityCore/issues) and merged pull requests
remain authoritative for issue completion. In particular, audit #281 is still open.

## Current capability assessment

| Capability | Repository implementation | Remaining boundary |
| --- | --- | --- |
| Control plane | Tenant/project/environment isolation, roles, API clients, versioned workflows/policies and administration | Complete outstanding historical reviews; broader enterprise hierarchy and delegated operations remain future scope |
| Provider routing | Immutable conditional routes by capability, country, document type and workflow; ordered fallback, bounded retries, timeouts and single-probe circuit recovery | Cost/tier optimization, arbitrary policy expressions and general asynchronous callbacks are not implemented |
| Provider setup | Versioned machine-readable manifests, encrypted environment credentials, organization-facing connection tests, production configuration diffs and independent activation approval | A connection test is not capability, deletion, retention or security certification |
| Signed custom providers | HMAC wire contracts, request/response verification, provider/environment-scoped shared replay claims and cross-runtime fixtures | Existing bearer configurations require explicit migration and re-testing; do not imply all providers use signed mode |
| Provider conformance | Executable Contract v1 fixtures and built-in adapter contract tests | Broad provider certification and a packaged multi-language Provider SDK remain incomplete |
| Workflows/policies/decisions | Published versions, immutable running snapshots, template instantiation idempotency, policy-driven decisions and maker-checker review | General cross-workload branching, compensation, policy language and signed attestations remain future work |
| Evidence | Captures, normalized provider checks, model provenance, immutable decision inputs, evidence reports and protected access | No generalized cross-workload evidence resource or public lineage API |
| Claims | Extracted fields and evidence-backed policy decisions | No reusable claims API; expiry, revocation, conflict resolution, selective disclosure and descendant propagation require a dedicated implementation |
| Manual review | Verification assignment, maker-checker, policy-bound reasons, tenant queues, skills/SLA routing and independent quality sampling; organization onboarding has its own escalation flow | Explicit `review_verification` role enforcement and migration are implemented on the remediation branch; protected review/merge remains tracked by #281. General verification-case escalation is not implemented; reviewer calibration/staffing assurance remain deployment responsibilities |
| Consent/privacy | Purpose-bound immutable consent, withdrawal, retention, legal holds and permission-controlled subject export/deletion with processing revocation | Historical unbound notification contacts and reports with lost references need controlled reconciliation; external processor deletion and legal assurance require accountable evidence |
| Tenant keys | Tenant data envelopes, resumable rotation, environment-scoped AWS KMS customer bindings and fail-closed key availability | Other KMS vendors and independent HSM integrations are not general plug-in capabilities |
| Tenant storage | Immutable tenant/environment routes to operator-approved buckets and residency regions; retained routes support old objects and restores | Routes share the approved deployment endpoint/identity; arbitrary tenant endpoints/credentials and automatic legacy relocation are not implemented |
| Audit | Append-only, authenticated hash chains, serialization and integrity verification | External WORM/SIEM connectors and independent assurance remain separate work |
| Developer platform | REST/OpenAPI, internal GraphQL, Python/JS/Java/.NET SDKs, CLI, generated models and live contract checks | Release publication and compatibility guarantees require versioned release evidence |
| Verification portal | Hosted consent/capture/liveness/review/result journeys, mobile handoff, localization, browser acceptance and real BFF transport checks | Physical-device, model and deployment certification are additional gates |
| Billing | GHS Paystack invoice checkout, authenticated reconciliation, refunds/disputes and recovery | Merchant test acceptance does not enable live collection or establish commercial release approval |
| Operations | Trace/metric redaction, SLO rules, synthetic load/restore drills, incident runbooks and release-evidence integrity gates | Real deployed capacity, restoration, paging, security/privacy review and accountable go-live approval remain required |

## Immediate engineering closure

The historical review inventory is tracked individually in
[the disposition register](../reviews/historical-review-dispositions.json). A closed or
resolved GitHub thread does not establish a fixed defect. Each pending finding needs
inspection against current code; confirmed defects need regressions and protected
remediation merges. Counts belong to the register rather than this document.

Hosted applicant attribution uses [signed subject metadata](../operations/subject-metadata.md).
Trusted ingress configuration is required before claiming applicant IP attribution;
User-Agent remains reported context. Historical proxy records must not be rewritten.

## Broader platform expansion

The next architectural capabilities are the generalized
[evidence service](evidence-model.md), [Claims Engine](claims-engine.md), broader provider
certification and asynchronous provider completion. These require complete domain,
authorization, privacy, lifecycle, OpenAPI and SDK contracts. Their architectural design
must not be presented as an implemented public API.

## Documentation authority

[ARCHITECTURE.md](../../ARCHITECTURE.md) defines the architectural vision; ADRs record
accepted decisions. Operational runbooks describe configured implementation boundaries.
OpenAPI defines concrete public endpoints. The
[platform roadmap](../foundation/platform-roadmap.md) separates implemented foundations,
future platform work and external release evidence.

Do not claim universal country/document coverage, arbitrary plug-and-play providers,
certified managed models, a provider marketplace, reusable verified claims or legal
compliance based only on repository tests or deployment configuration.

The repository owner selected proprietary, all-rights-reserved licensing on
2026-10-19. See [LICENSE](../../LICENSE); this does not alter third-party licenses.
