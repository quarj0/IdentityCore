# Product Alignment and Gap Assessment

Last reviewed: 2026-10-20

IdentityCore is a vendor-neutral identity infrastructure platform with a working
identity verification workload. Repository implementation, historical review closure,
and deployment assurance are separate milestones. The live
[issue tracker](https://github.com/quarj0/IdentityCore/issues) and merged pull requests
remain authoritative for issue completion. PRs #433 and #434 are merged. Audit #281 is closed with the
[completed reconciliation](../reviews/README.md). New feedback still requires
individual assessment and protected remediation.

## Current capability assessment

| Capability | Repository implementation | Remaining boundary |
| --- | --- | --- |
| Control plane | Tenant/project/environment isolation, roles, API clients, versioned workflows/policies and administration | Broader enterprise hierarchy and delegated operations remain future scope |
| Provider routing | Immutable conditional routes by capability, country, document type and workflow; ordered fallback, bounded retries, timeouts and single-probe circuit recovery | Cost/tier optimization, arbitrary policy expressions remain future scope; signed durable async callbacks/polling are implemented |
| Provider setup | Versioned machine-readable manifests, encrypted environment credentials, organization-facing connection tests, production configuration diffs and independent activation approval | A connection test is not capability, deletion, retention or security certification |
| Signed custom providers | HMAC wire contracts, request/response verification, provider/environment-scoped shared replay claims and cross-runtime fixtures | Existing bearer configurations require explicit migration and re-testing; do not imply all providers use signed mode |
| Provider conformance | Versioned scope-bound assurance reports, independent approval/revocation, packaged Python/JS/Java/.NET Provider SDKs and 17-case HTTP/worker conformance | Actual deployment/model/security certification requires independently verified evidence |
| Workflows/policies/decisions | Published versions, immutable running snapshots, template instantiation idempotency, policy-driven decisions and maker-checker review | General cross-workload branching, compensation, policy language and signed attestations remain future work |
| Evidence | Versioned cross-workload resources, encrypted payloads/provenance, provider-check origins, purpose grants, bounded public lineage, supersession and lifecycle propagation | Signed third-party attestations and unrestricted raw exports are outside the implemented contract |
| Claims | Public versioned deterministic claims, expiry/revocation, source-bound freshness, independent conflict decisions, approved reuse policies and audience-bound field disclosure | Credential issuance and zero-knowledge selective disclosure remain separate capabilities |
| Manual review | Verification assignment, maker-checker, policy-bound reasons, tenant queues, skills/SLA routing and independent quality sampling; organization onboarding has its own escalation flow | Explicit `review_verification` enforcement and the narrow system-role migration are merged in #433. General verification-case escalation is not implemented; reviewer calibration/staffing assurance remain deployment responsibilities |
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
resolved GitHub thread does not establish a fixed defect. The 2026-10-20
reconciliation inspected all closed/merged PR feedback against main and records
merge receipts and regression evidence. No actionable or pending finding remains
in that snapshot. New feedback still requires individual assessment and protected
remediation. Counts belong to the register rather than this document.

Hosted applicant attribution uses [signed subject metadata](../operations/subject-metadata.md).
Trusted ingress configuration is required before claiming applicant IP attribution;
User-Agent remains reported context. Historical proxy records must not be rewritten.

## Governed platform capabilities

The generalized [evidence service](evidence-model.md), [Claims Engine](claims-engine.md),
provider assurance and asynchronous completion now have implemented domain,
authorization, lifecycle, OpenAPI and four-language SDK contracts. Their runbooks
are [governed resources](../operations/governed-resources.md) and
[provider operations](../operations/provider-operations.md). The generalized APIs
coexist with verification-specific capture/check/decision records; they do not
retroactively turn every historical extracted field into an approved reusable claim.

Additional workflow branching/compensation, infrastructure vendors, signed credential
formats, marketplaces and representative deployment assurance remain separate scope.

## Documentation authority

[ARCHITECTURE.md](../../ARCHITECTURE.md) defines the architectural vision; ADRs record
accepted decisions. Operational runbooks describe configured implementation boundaries.
OpenAPI defines concrete public endpoints. The
[platform roadmap](../foundation/platform-roadmap.md) separates implemented foundations,
future platform work and external release evidence.

Do not claim universal country/document coverage, arbitrary plug-and-play providers,
certified managed models, a provider marketplace, unconditionally verified claims or legal
compliance based only on repository tests or deployment configuration.

The repository owner selected proprietary, all-rights-reserved licensing on
2026-10-19. See [LICENSE](../../LICENSE); this does not alter third-party licenses.
