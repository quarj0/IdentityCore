# IdentityCore Platform Roadmap

Last reviewed: 2026-10-20

IdentityCore is vendor-neutral identity infrastructure. Identity verification is its
first workload. This roadmap separates repository foundations, immediate engineering
closure, future platform work and deployment assurance. The
[implementation backlog](../planning/implementation-backlog.md) defines stable work IDs;
GitHub issues and merged pull requests determine their completion state.

## Implemented foundations

| Area | Current execution paths | Implementation references |
| --- | --- | --- |
| Platform kernel | Tenant/project/environment isolation, API credentials, MFA and sessions, invitations, quotas and administration | [Architecture](../../ARCHITECTURE.md), [quota operations](../operations/api-usage-quotas.md) |
| Provider platform | Manifest v1, organization setup, environment credentials, connection probes and independent production activation | [Manifests](../architecture/provider-manifests.md), [setup](../operations/provider-setup.md) |
| Provider execution | Conditional routes, ordered fallback, bounded attempts/timeouts, circuit recovery, health inspection, normalized versioned results and Contract v1 fixtures | [Runtime](../architecture/provider-runtime.md), [resilience](../operations/provider-route-resilience.md) |
| Workflow/policy/decision | Published versions and templates, immutable snapshots, idempotent instantiation, controlled outcomes and maker-checker review | [Instantiation](../operations/workflow-template-instantiation.md) |
| Evidence/privacy | Captures, provider evidence, reports, purpose-bound consent/withdrawal, retention, legal holds, subject exports and deletion | [Evidence](../architecture/evidence-model.md), [consent](../operations/purpose-consent.md) |
| Manual review | Verification assignment/maker-checker, policy-bound reasons, tenant queues, skills/SLA routing and quality sampling; separate organization onboarding escalation | [Queues](../operations/review-queues.md), [quality](../operations/review-quality.md) |
| Storage/keys | Immutable approved-bucket routing, tenant data envelopes, resumable rotation and environment-scoped AWS KMS customer keys | [Storage](../operations/tenant-storage.md), [keys](../operations/customer-kms.md) |
| Developer surfaces | REST/OpenAPI, internal GraphQL, Python/JS/Java/.NET SDKs, CLI, generated models and live contract checks | [API](../architecture/api-spec.md), [Provider SDK](../providers/provider-sdk.md) |
| Hosted verification | Consent, camera/document/selfie/liveness, handoff, locale negotiation, retry/review/final states, browser fixtures and real BFF transport checks | [Portal](../../frontend/verification-portal/README.md) |
| Operations | Durable processing jobs, redacted telemetry, SLO rules, synthetic load/restore drills, incident records and release-evidence integrity gates | [Recovery](../operations/processing-job-recovery.md), [release gates](../operations/release-evidence-gate.md) |
| Billing | GHS Paystack invoice checkout/reconciliation, subscription intervals, refunds/disputes and bounded recovery | [Billing](../operations/billing-foundation.md) |

These paths have repository implementations and automated coverage. They do not imply
that every historical finding is resolved or that any deployment/provider is certified.

## Immediate engineering closure

The four immediate items merged in [PR #433](https://github.com/quarj0/IdentityCore/pull/433):
signed BYOP transport (including authenticated errors and shared replay protection),
trusted hosted applicant metadata, historical review remediation, and synchronized
documentation with proprietary/all-rights-reserved licensing.

The [audit reconciliation](../reviews/README.md) inventories all closed/merged PR
feedback against merged main. No actionable or pending finding remains in that
snapshot. The receipt merged in PR #434 and issue #281 is closed.
Future feedback still requires individual evidence and protected merge; neither
thread resolution nor a clean test suite alone establishes closure.

## Governed platform extension

- **Generalized evidence:** implemented public resources, immutable bounded schemas,
  purpose grants, encrypted provenance, lineage, supersession and privacy lifecycle.
- **Reusable claims:** implemented deterministic versioned rules, source-bound freshness,
  explicit independent conflict resolution, revocation and audience-bound disclosure.
- **Provider ecosystem:** implemented scoped assurance proposal/approval/revocation,
  durable signed callback/polling operations and Python/JS/Java/.NET Provider SDKs.

See [governed resources](../operations/governed-resources.md),
[provider operations](../operations/provider-operations.md) and the
[SDK package index](../../provider-sdk/README.md). Synthetic conformance artifacts
prove SDK protocol behavior, not deployment or independent provider assurance.

## Further platform scope

- **Workflow generalization:** cross-workload branching, compensation and policy expressions.
- **Infrastructure expansion:** additional storage/KMS vendors, independently integrated
  HSMs, WORM/SIEM exports, signed checkpoints and attestations.
- **Future workloads:** authorized registry identity resolution, age/eligibility assertions,
  credential validation/issuance, account recovery and organization identity.

These are future capabilities. Published designs and sample envelopes do not establish
implemented public contracts. Country/document expansion requires supported provider
contracts and representative evaluation; a provider marketplace is not implemented.

## Deployment and assurance gates

Complete independent security/privacy/accessibility review, representative model and
attack evaluation, physical-device acceptance, deployed inference capacity, provider
agreements/residency, restoration, pager delivery, incident exercises and accountable
pilot approval. Commercial release additionally needs payment and legal/terms evidence.

The [release-evidence gate](../operations/release-evidence-gate.md) checks evidence
integrity, freshness and release-head binding. It cannot create or authenticate the
underlying human/provider assurances. Synthetic fixtures are not production evidence.
