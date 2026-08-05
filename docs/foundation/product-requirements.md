# Product Requirements

## 1. Product definition

IdentityCore is a vendor-neutral identity infrastructure platform. Identity verification is the first implemented workload on the platform.

The product provides reusable infrastructure and orchestration primitives for identity operations, including provider runtime, capability contracts, evidence, policies, decisions, manual review, privacy controls, audit, SDKs, and CLI.

Applications integrate once with IdentityCore. IdentityCore orchestrates managed, commercial, government, customer-hosted, and supporting infrastructure providers through stable capability contracts and workflow/policy execution.

## 2. Platform users and stakeholders

- Platform Administrators: manage the IdentityCore deployment, security, audit, and platform settings.
- Tenant/Organization Administrators: govern their organization, projects, environments, workflows, policies, providers, and API clients.
- Verification Officers / Reviewers: perform Manual Review, maker-checker approvals, and reviewer actions.
- API Clients / Applications: integrate with IdentityCore through REST APIs, SDKs, CLI, or hosted journeys.
- Verification Subjects: individuals or entities whose identity is being verified.
- Provider implementers: operators of managed, commercial, government, or customer-hosted providers.
- Compliance and security officers: govern privacy, retention, deletion, export, and audit requirements.

## 3. Platform requirements

IdentityCore must support:

- tenants, organizations, projects, and environments;
- users, roles, API clients, and scopes;
- workflow versions and immutable workflow snapshots;
- policy versions and immutable policy snapshots;
- provider registrations, capability declarations, and provider assignments;
- provider routes or assignments for capability resolution;
- evidence collection, normalization, lineage, retention, deletion, and export;
- claims foundations and decision inputs;
- decisions and decision recording;
- audit and tamper-evident operational event logging;
- webhooks and notification delivery;
- SDKs and CLI for application integration;
- privacy controls for consent, legal holds, and subject rights;
- multi-tenancy and environment isolation;
- REST API, internal GraphQL, and documentation surfaces.

The current implementation includes foundations for many of these requirements, with advanced provider routing, broad provider discovery, reusable claim lifecycle, and marketplace capabilities still evolving.

## 4. Identity verification workload requirements

Identity verification is the first workload built on IdentityCore. It must be described as a workload that composes platform primitives, not as the entire product.

Identity verification requirements include:

- secure verification request creation;
- verification session creation and subject-facing workflow;
- identity subject context and access control;
- consent capture and recording;
- country/document selection and document definition support;
- document capture, image quality, classification, and OCR capabilities;
- selfie capture, liveness, face comparison, and PAD where applicable;
- evidence normalization, versioning, and lineage;
- policy evaluation and decision engine execution;
- Manual Review, reviewer assignment, and maker-checker controls;
- signed webhooks, notifications, and result delivery;
- retention, export, deletion, and legal-hold controls;
- audit and operational logging.

The current codebase implements a working identity verification vertical slice, but it does not imply that every identity or document use case is complete or production-certified.

## 5. Provider requirements

Provider integration must be governed by capability contracts rather than provider-specific workflow logic.

Provider requirements include:

- provider-neutral capability contracts;
- support for IdentityCore Managed Providers, commercial providers, government/authoritative providers, and customer-hosted providers;
- provider authentication and secure credential handling;
- signed provider requests and message integrity;
- timestamps, nonces, and replay resistance;
- idempotency semantics for retries and duplicate invocation handling;
- explicit timeout enforcement;
- response-size limits and schema validation;
- normalized result semantics and stable status codes;
- telemetry redaction and safe diagnostics;
- provider versioning and adapter metadata;
- health and readiness indicators;
- data residency and processing declarations;
- future conformance testing and manifest-driven onboarding.

The current implementation has a provider registry, adapter resolution, secure HTTP provider calls, signing, replay protection, normalized results, and provider-check persistence. Full provider marketplace discovery, fallback route composition, and provider conformance tooling remain planned.

## 6. Evidence and claims requirements

Evidence requirements include:

- provenance for evidence sources and provider input;
- capability, provider, adapter, model, workflow, and policy versions;
- normalized outputs, confidence, and quality metadata;
- integrity metadata and lineage references;
- retention classification, deletion state, and access controls;
- minimal access to sensitive evidence;
- evidence snapshots used by decisions.

Claims requirements include:

- claims that remain linked to supporting evidence and policy;
- extracted claims, provider-asserted claims, normalized claims, derived claims, and policy-satisfied claims;
- mapping of provider output into stable IdentityCore claim schemas;
- provenance and status for each claim;
- explicit statement that a generalized reusable Claims Engine is not yet fully complete;
- ability to use claims in policy evaluation while preserving evidence-driven auditability.

## 7. Workflow, policy, and decision requirements

IdentityCore must support:

- workflow definitions that describe required capability and review steps;
- immutable workflow snapshots for running executions;
- policy definitions and snapshotting;
- decision input snapshots that preserve the evidence and workflow/policy context;
- policy-driven required capabilities, thresholds, and review rules;
- decisions as recorded outcomes, not provider responses alone;
- explicit support for automatic outcomes, manual outcomes, and uncertain results;
- review procedures for fallback and retry decisions.

The platform should preserve historical workflow and policy meaning through immutable snapshots.

## 8. Manual review requirements

Manual Review must be a governed execution path, with:

- authorized reviewer roles and permission checks;
- reviewer assignment and workload management;
- evidence access scoped to the case;
- reason codes, notes, and escalation;
- maker-checker approval where required;
- immutable review actions and audit records;
- explicit handling for review authorization failures.

Current implementation foundations include reviewer assignment, manual decision recording, maker-checker controls, and audit history.

## 9. Privacy and compliance requirements

Platform privacy requirements include:

- consent capture and purpose limitation;
- minimal data collection for declared use cases;
- configurable retention policies;
- deletion of retained media and subject data where permitted;
- export and data portability support;
- legal-hold handling;
- pseudonymization and de-identification where appropriate;
- audit preservation of access and actions;
- biometric evidence handling with explicit consent and restricted access;
- clear distinction of IdentityCore versus customer responsibilities;
- managed provider versus external provider responsibilities;
- processor/subprocessor considerations and provider data residency declarations.

The platform should not claim regulatory certification based on controls alone.

## 10. Security requirements

IdentityCore security requirements include:

- strong authentication and RBAC;
- tenant and environment isolation;
- secure provider invocation and request signing;
- endpoint validation and SSRF protection;
- egress allowlists and DNS/TLS validation;
- timestamp/nonces/replay protection;
- idempotency and retry controls;
- schema validation and response-size limits;
- encrypted provider credentials;
- audit logging for provider configuration and invocation;
- protection for evidence access and sensitive data.

The repository currently implements many of these foundations, with hardening and broader operational assurance still required.

## 11. Developer platform requirements

The platform must provide:

- public REST APIs for applications;
- internal GraphQL for dashboards;
- SDKs and CLI for integration and automation;
- developer documentation and examples;
- stable versioning guidance;
- API clients and secret rotation;
- hosted journeys and developer portal content;
- webhook configuration and delivery;
- sandbox and production environment separation.

## 12. Operational requirements

Operational requirements include:

- monitoring and observability for provider selection, invocation, latency, failures, and audit events;
- retention and deletion jobs;
- webhook delivery retries and status tracking;
- backup and recovery planning;
- deployment configuration for Redis, PostgreSQL, object storage, and managed provider host;
- migration and compatibility controls.

## 13. Non-functional requirements

Non-functional requirements include:

- security and privacy by design;
- clear separation between platform infrastructure and workload-specific logic;
- horizontal scalability through stateless services and background processing;
- reliability and fault isolation;
- maintainable modular architecture;
- comprehensive documentation;
- clear distinction between implemented foundations, partial features, and planned work.

## 14. Current scope

Current scope includes:

- vendor-neutral identity infrastructure platform foundations;
- identity verification workload as the first implemented vertical slice;
- tenant, project, and environment isolation;
- workflows, policies, and decision snapshots;
- provider runtime, provider records, and provider checks;
- IdentityCore Managed Provider host for selected capabilities;
- REST APIs, internal GraphQL, SDKs, CLI, and frontend applications;
- evidence normalization, audit, retention, deletion, and export.

## 15. Out of scope

Out of scope for the current implementation includes:

- broad provider marketplace and automated onboarding;
- complete reusable cross-workload Claims Engine;
- tenant-routed storage and customer-managed key routing end to end;
- full regulatory certification;
- every country or document type;
- production-grade managed model accuracy guarantees;
- general offline verification or wallet issuance;
- unsupported biometric modalities such as fingerprints or iris recognition;
- developer SDKs for all possible languages.

## 16. Future workloads

Future workloads may include:

- reusable verified claims and selective disclosure;
- registry-backed identity resolution and authoritative lookup;
- credential issuance and validation;
- step-up identity checks and account recovery;
- organizational identity;
- eligibility or age assertions;
- program-specific trust workflows for financial, healthcare, education, and government use cases.

These are platform directions rather than claims that the current repository already delivers.

## Performance

Target response times:

- Authentication: < 300 ms
- Verification creation: < 500 ms
- Face matching: < 3 seconds
- Verification result: < 5 seconds

---

## Scalability

The platform shall support horizontal scaling through stateless services and asynchronous background processing.

---

## Reliability

Target uptime:

99.9%

---

## Privacy

The platform shall:

- Collect only necessary data.
- Support consent workflows.
- Support configurable retention policies.
- Allow deletion of retained media after policy expiry.

---

## Maintainability

The platform shall:

- Follow clean architecture principles.
- Support automated testing.
- Use API versioning.
- Maintain comprehensive documentation.

---

## Out of Scope (Version 1.0)

The following features are intentionally excluded:

- Government database integrations
- Passport verification
- Document Type verification
- Driver's licence verification
- Fingerprint recognition
- Iris recognition
- Criminal records
- Immigration services
- Hospital integrations
- Payment processing
- Mobile applications
- AI fraud prediction
- Offline verification
- Digital identity wallet
- SDKs for all languages

These features remain part of the long-term roadmap.

---

## MVP Deliverables

Version 1.0 will deliver:

- Multi-tenant platform
- Authentication
- Organization management
- Verification workflows
- Document upload
- OCR
- Selfie capture
- Liveness detection
- Face matching
- Verification decisions
- Audit logs
- REST API
- Webhooks
- Admin dashboard
- Developer documentation

---

## Acceptance Criteria

IdentityCore Version 1.0 is complete when an organization can:

1. Register an organization.
2. Create a verification request.
3. Send the verification link to an Verification Subject.
4. Receive user consent.
5. Receive document upload.
6. Receive selfie capture.
7. Perform liveness detection.
8. Perform facial matching.
9. Receive a verification decision.
10. Receive webhook notifications.
11. Review audit logs.
12. Integrate successfully using the public REST API.

---

## Product Philosophy

IdentityCore is not a facial recognition application.

It is an identity infrastructure platform.

Every feature added to the platform must strengthen trust, improve security, preserve privacy, or simplify identity verification for organizations and the individuals they serve.
