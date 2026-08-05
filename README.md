# IdentityCore

> **Vendor-neutral identity infrastructure for building, orchestrating, and governing digital trust workloads.**

IdentityCore provides a common platform for identity workflows, provider execution,
evidence, claims, policy, decisions, human review, privacy controls, and audit.

**Identity verification is the first workload built on the platform. It is not the
platform boundary.**

Organizations integrate with one stable IdentityCore contract and choose which providers
execute each capability. A provider may be operated by IdentityCore, supplied by a
commercial IDV vendor, exposed by an authorized registry, hosted by the customer, or
provided by supporting infrastructure such as object storage, KMS/HSM, risk, or
messaging systems.

IdentityCore is designed to reduce integration fragmentation and provider lock-in while
preserving tenant isolation, policy control, evidence lineage, and auditability.

## What the platform provides

- **Provider Runtime** — resolves, invokes, secures, observes, and normalizes capability providers.
- **Workflow Engine** — composes identity capabilities and human steps into versioned workloads.
- **Policy Engine** — determines evidence requirements, thresholds, routing, and review rules.
- **Evidence Model** — records source, provenance, confidence, version, integrity, and retention.
- **Claims** — represents normalized and derived statements linked to supporting evidence.
- **Decision Engine** — records policy-driven outcomes from immutable decision inputs.
- **Manual Review** — supports governed reviewer assignment, escalation, and maker-checker controls.
- **Audit and Compliance** — provides append-only, tamper-evident activity records and exports.
- **Privacy Controls** — supports consent, retention, legal holds, subject export, and deletion.
- **Multi-tenancy** — isolates organizations, projects, environments, users, data, and providers.
- **APIs, SDKs, CLI, and Webhooks** — expose stable integration surfaces for applications and operators.

## Platform architecture

```text
Applications, SDKs, CLI, hosted journeys and operator consoles
                              |
                              v
                     IdentityCore API Layer
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
       Control Plane                    Execution Plane

  Tenants and projects             Workflow Engine
  Environments                     Policy Engine
  Users, roles and API clients     Provider Runtime
  Workflow definitions             Evidence and Claims
  Policy versions                  Decision Engine
  Provider configuration           Manual Review
  Privacy and retention            Audit and event delivery
             |                                 |
             +----------------+----------------+
                              |
                              v
                           Providers

  IdentityCore Managed Providers | Commercial IDV vendors
  Government registries | Customer-hosted services
  Risk | Storage | KMS/HSM | Messaging providers
```

Read the [canonical architecture](ARCHITECTURE.md) for the complete platform model.

## IdentityCore Managed Providers

The FastAPI AI service hosts IdentityCore-managed implementations for selected
capabilities such as document quality, document classification, OCR, face comparison,
liveness, and presentation-attack detection.

These are **Managed Providers**, not privileged architectural components. Core workflow
and decision domains depend on provider and capability contracts rather than directly on
PaddleOCR, InsightFace, OpenCV, MediaPipe, or any commercial vendor API.

Customers should be able to replace a managed capability with a conforming commercial,
government, or customer-hosted provider without changing their application integration.

## First workload: identity verification

The current working vertical slice composes platform primitives into a verification
journey that includes:

- verification subjects and secure sessions;
- consent and purpose capture;
- country and document selection;
- document upload, validation, quality, classification, and OCR;
- selfie capture, liveness/PAD, and face comparison;
- versioned workflows, policy snapshots, and decision inputs;
- retry, failure, and Manual Review paths;
- reviewer assignment and maker-checker decisions;
- signed webhooks and notifications;
- evidence access, audit, retention, export, and deletion controls.

The existence of this workload does not require future identity workloads to use document
or biometric verification.

## Current status

IdentityCore is an actively developed, **pre-production identity infrastructure platform
with a working identity-verification vertical slice**.

Implemented foundations include:

- tenant, project, and environment isolation;
- REST APIs and internal GraphQL surfaces;
- versioned workflows and verification policies;
- provider registry, capability adapters, and provider assignments;
- centralized provider invocation and normalized provider checks;
- secure HTTP provider calls, message signing, nonce binding, and replay protection;
- redacted provider telemetry, duration tracking, and versioned results;
- immutable workflow and decision snapshots;
- Manual Review assignment and maker-checker controls;
- tamper-evident audit events;
- retention deletion, legal holds, subject exports, and subject deletion;
- Python, Java, and .NET SDKs and a Python CLI;
- organization, developer, verification, marketing, and platform-admin frontends.

Important work remains before broad production use, including richer conditional provider
routes and ordered fallback chains, provider conformance tooling, organization-facing
provider onboarding, tenant-routed storage and customer-managed keys, broader claims
lifecycle support, formal assurance, production model validation, and operational
hardening.

See the [product alignment and gap assessment](docs/architecture/product-alignment.md)
for capability-level maturity.

## Repository structure

```text
backend/
├── django/                  # Core control and execution plane
└── ai-service/              # IdentityCore Managed AI Providers

frontend/
├── dashboard/               # Organization operations
├── identitycore/            # Public/marketing application
├── platform-admin/          # Platform administration
├── verification-portal/     # Hosted subject journey
└── developer-portal/        # API, SDK, CLI and integration docs

sdk/
├── python/
├── java/
└── dotnet/

docs/
├── foundation/
├── architecture/
├── decisions/
├── planning/
├── research/
└── notes/

infrastructure/
├── docker/
├── nginx/
└── scripts/
```

## Technology stack

### Core platform

- Python and Django
- Django REST Framework
- GraphQL for internal application surfaces
- Celery and Redis
- PostgreSQL
- S3-compatible object storage

### Managed AI Providers

- FastAPI
- OpenCV
- ONNX Runtime
- InsightFace
- PaddleOCR
- MediaPipe where applicable

### Frontend and developer tooling

- Next.js, React, TypeScript, Tailwind CSS
- Python, Java, and .NET SDKs
- Python CLI

### Infrastructure

- Docker and Docker Compose
- Nginx
- GitHub Actions

## Documentation map

### Start here

- [Canonical Architecture](ARCHITECTURE.md)
- [Vision](docs/foundation/vision.md)
- [Product Requirements](docs/foundation/product-requirements.md)
- [Roadmap](docs/foundation/roadmap.md)
- [Glossary](docs/foundation/glossary.md)

### Platform architecture

- [Current System Architecture](docs/architecture/architecture.md)
- [Provider Runtime](docs/architecture/provider-runtime.md)
- [Capability Model](docs/architecture/capability-model.md)
- [Evidence Model](docs/architecture/evidence-model.md)
- [Claims Engine](docs/architecture/claims-engine.md)
- [Product Alignment and Gap Assessment](docs/architecture/product-alignment.md)
- [Database Design](docs/architecture/database-design.md)
- [API Specification](docs/architecture/api-spec.md)

### Trust, operations, and implementation

- [Security](docs/architecture/security.md)
- [Threat Model](docs/architecture/threat-model.md)
- [Compliance](docs/architecture/compliance.md)
- [AI / Managed Provider Design](docs/architecture/ai-design.md)
- [Deployment](docs/architecture/deployment.md)
- [Testing Strategy](docs/architecture/testing-strategy.md)
- [Coding Standards](docs/architecture/coding-standards.md)
- [Architecture Decision Records](docs/decisions/)
- [Implementation Backlog](docs/planning/implementation-backlog.md)

Some filenames may evolve as the documentation is consolidated. The canonical
architecture and ADRs determine architectural meaning; OpenAPI remains the source of
truth for concrete public endpoints.

## Production startup configuration

Local development uses the clearly marked sample values in `.env.example`. Before
starting Django with `DJANGO_SETTINGS_MODULE=config.settings.production`, provide:

- independent, randomly generated `DJANGO_SECRET_KEY` of at least 50 characters and
  `JWT_SIGNING_KEY` of at least 64 characters;
- a random `AI_SERVICE_SHARED_TOKEN` of at least 32 characters;
- explicit `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_HOST`, and a non-default random
  `POSTGRES_PASSWORD` of at least 16 characters; and
- production hostnames in `DJANGO_ALLOWED_HOSTS`, with `DJANGO_DEBUG` disabled.

Production settings validate these requirements during import and stop startup when
configuration is missing or unsafe. Errors name configuration variables, never secret
values.

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Running all tests

After installing the repository's Python, Node/pnpm, Playwright, Java, and .NET
dependencies, run every backend, managed-provider, frontend, and SDK test suite from the
repository root:

```bash
make test-all
```

The command prints each suite and stops at the first failure. Use the component-specific
commands in `.github/workflows/ci.yml` to install dependencies or troubleshoot a single
suite.

## Roadmap direction

Development is organized around platform capability maturity rather than treating AI or
identity verification as the whole product:

1. Harden the platform kernel, isolation, privacy, audit, and operational controls.
2. Complete Provider Runtime routing, fallback, health, and conformance.
3. Expand workflow, policy, decision, evidence, and claims capabilities.
4. Improve SDKs, CLI, hosted journeys, and developer experience.
5. Certify the identity-verification workload for supported countries and providers.
6. Add provider ecosystem and organization self-service operations.
7. Introduce future workloads using the same platform primitives.

## Engineering principles

- Business logic belongs in domain services.
- Tenant and environment isolation are mandatory.
- Public APIs expose prefixed public IDs, never internal database IDs.
- Workloads depend on capability contracts, not provider-specific clients.
- Provider output is evidence, not the final organizational decision.
- Workflow, policy, provider, evidence, model, and decision versions remain auditable.
- Unknown, unsupported, malformed, or inconclusive evidence fails safely or enters review.
- Security, privacy, tests, migrations, and documentation are part of feature completion.

## Security and responsible use

IdentityCore processes sensitive identity documents, personal information, biometric
evidence, credentials, and audit records. Deployments must apply least privilege,
defense in depth, secure secret management, encryption, monitoring, backups, retention,
incident response, and jurisdiction-appropriate legal controls.

IdentityCore must not be used to justify unaudited, fully autonomous high-impact
decisions. Organizations remain responsible for their legal basis, policies, provider
selection, reviewer governance, and consequences of a decision.

## Contributing

Contributions should:

- begin on a feature branch and be submitted through a pull request;
- read `ARCHITECTURE.md` and relevant ADRs before changing platform boundaries;
- preserve tenant and environment isolation;
- use capability/provider interfaces rather than introducing vendor coupling;
- include appropriate tests and migrations;
- update OpenAPI, SDKs, and documentation when contracts change;
- add or supersede an ADR for significant architectural decisions;
- avoid mixing unrelated changes in one pull request.

See the repository contribution and coding-standard documents for component-specific
commands and review expectations.

## License

License information will be added before the first formal public release.

## Project statement

IdentityCore is building the infrastructure that allows organizations to compose,
operate, and govern trusted identity capabilities without surrendering their architecture
to one verification vendor.
