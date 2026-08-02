# IdentityCore

> IdentityCore is an enterprise digital identity infrastructure platform. Version 1.0 delivers secure identity verification while establishing the foundation for trusted digital identity services across organizations and governments.

IdentityCore is a multi-tenant **identity infrastructure and orchestration platform**.
Organizations use its common control plane, APIs, workflows, evidence model, policy
engine, audit trail, and provider ecosystem to build identification and digital-trust
services. Document capture, biometric verification, liveness detection, and
policy-driven decisions are the first workload running on that infrastructure; they are
not the boundary of the product.

Like a cloud platform offers common infrastructure while customers choose managed or
third-party services, IdentityCore is intended to let organizations compose
IdentityCore-managed capabilities, their own internal systems, and specialist identity
providers behind one stable contract. A document, biometric, registry, storage, risk,
or notification vendor can therefore participate as a provider instead of being treated
only as a competing end-to-end product.

The platform is designed with security, privacy, auditability, and scalability as first-class principles. While the initial target market is Ghana, IdentityCore is built to support multiple countries through configurable Country Profiles, Verification Policies, and Provider Adapters rather than country-specific business logic.

---

## Vision

To provide the trusted infrastructure on which organizations can build secure,
privacy-preserving, interoperable, and auditable identification services.

IdentityCore's first complete service is identity verification, but its platform boundary
is broader: reusable identity workflows, provider orchestration, evidence and claims,
policy enforcement, consent, lifecycle controls, and digital-trust services for
enterprises, financial institutions, educational institutions, healthcare providers,
and governments.

---

## Core Principles

- Security by Default
- Privacy by Design
- Multi-Tenant Architecture
- AI as Evidence, Not Decision Maker
- API-First Design
- Auditability
- Extensibility
- Country-Agnostic Architecture

---

## Technology Stack

## Backend

- Python
- Django
- Django REST Framework
- GraphQL (Internal)
- Celery
- PostgreSQL
- Redis

## AI Service

- FastAPI
- OpenCV
- ONNX Runtime
- InsightFace
- PaddleOCR
- MediaPipe (where applicable)

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Infrastructure

- Docker
- Docker Compose
- GitHub Actions
- Nginx
- Object Storage (S3-compatible)

---

## Repository Structure

```text
identitycore/

backend/
├── django/
└── ai-service/

frontend/
├── dashboard/
├── identitycore/
├── platform-admin/
├── verification-portal/
└── developer-portal/

infrastructure/
├── docker/
├── nginx/
└── scripts/

docs/
├── foundation/
├── architecture/
├── decisions/
├── research/
└── notes/
```

---

## Project Documentation

## Foundation

- Vision
- Product Requirements
- Roadmap
- Glossary

## Architecture

- Architecture
- Database Design
- API Specification
- AI Design
- Deployment
- Security
- Compliance
- Threat Model
- Coding Standards
- Testing Strategy

## Decisions

Architecture Decision Records (ADRs) document significant technical decisions made throughout the project.

## Research

Technical investigations, comparisons, and experiments that inform architectural decisions.

## Notes

General ideas, future enhancements, lessons learned, and project observations.

---

## Key Features

Version 1.0 includes:

- Multi-tenant architecture
- Organization management
- Platform Users and Role-Based Access Control
- Verification Subjects
- Verification Sessions
- Consent management
- Identity Document processing
- Face detection
- Face matching
- Passive liveness detection
- OCR
- Verification Policies
- Manual Review
- Audit logging
- Webhooks
- REST API
- Internal GraphQL API

---

## Project Status

Current phase: **working vertical slice, pre-production**.

The repository now contains implemented Django, AI-service, and frontend foundations,
including the core verification journey. It is not yet a production-complete version of
the full product vision. In particular, Bring Your Own Provider currently has a provider
registry, tenant assignments, normalized check records, and notification adapters, but
does not yet provide general custom-provider execution, conditional routing, ordered
fallback chains, tenant-owned storage, or customer-managed encryption keys.

See the [product alignment and gap assessment](docs/architecture/product-alignment.md)
for a capability-by-capability statement of what exists and what remains.

### Production startup configuration

Local development uses the clearly marked sample values in `.env.example`. Before
starting Django with `DJANGO_SETTINGS_MODULE=config.settings.production`, provide:

- independent, randomly generated `DJANGO_SECRET_KEY` (at least 50 characters) and
  `JWT_SIGNING_KEY` (at least 64 characters);
- a random `AI_SERVICE_SHARED_TOKEN` (at least 32 characters);
- explicit `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_HOST`, and a non-default random
  `POSTGRES_PASSWORD` (at least 16 characters); and
- production hostnames in `DJANGO_ALLOWED_HOSTS`, with `DJANGO_DEBUG` disabled.

Production settings validate these requirements during import and stop startup with
configuration variable names—not secret values—when configuration is missing or unsafe.
For example, generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

### Running all tests

After installing the repository's Python, Node/pnpm, Playwright, Java, and .NET
dependencies, run every backend, AI, frontend, and SDK test suite from the repository
root with:

```bash
make test-all
```

The command prints a named heading and pass/fail result for each suite and stops at the
first failure. Use the component-specific commands in `.github/workflows/ci.yml` when
installing dependencies or troubleshooting an individual suite.

---

## Development Roadmap

Implementation will follow this sequence:

1. Repository and infrastructure
2. Django foundation
3. FastAPI AI service
4. Database and background processing
5. Identity domain
6. Verification domain
7. AI integration
8. Frontend applications
9. Production readiness
10. Pilot deployment

---

## Engineering Principles

IdentityCore follows these engineering principles:

- Business logic belongs in the service layer.
- Tenant isolation is mandatory.
- Public APIs expose Public IDs (prefixed ULIDs), never internal database IDs.
- AI provides technical evidence only; business decisions are made by the Decision Engine.
- Security, testing, and documentation are part of every feature—not afterthoughts.

---

## Security

IdentityCore handles highly sensitive information including identity documents and biometric data.

Every component is designed around:

- Zero Trust
- Least Privilege
- Defense in Depth
- Encryption
- Auditability
- Secure Defaults

Security is considered a core product feature.

---

## Contributing

As the project grows, all contributions should:

- Follow the Coding Standards.
- Include appropriate tests.
- Maintain tenant isolation.
- Preserve API compatibility where applicable.
- Update documentation when behavior changes.
- Record major architectural decisions as ADRs.

---

## License

License information will be added before the first public release.

---

## Contact

IdentityCore is currently under active development.

For questions, feature requests, or future collaboration, project contact information will be added when the platform enters its first public preview.

---

## Final Statement

IdentityCore is being built as long-term identity infrastructure rather than a single-purpose application.

Every architectural decision aims to balance security, privacy, scalability, maintainability, and developer experience while enabling organizations to perform trustworthy identity verification across multiple jurisdictions.
