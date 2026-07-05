# Contributing to IdentityCore

Thank you for your interest in contributing to IdentityCore.

IdentityCore is a security-first identity verification platform. Every contribution should prioritize security, privacy, maintainability, and reliability over speed or convenience.

Please read this guide before contributing.

---

# Code of Conduct

All contributors are expected to:

- Be respectful and professional.
- Welcome constructive feedback.
- Focus discussions on technical solutions.
- Respect the privacy and security goals of the project.
- Avoid introducing unnecessary complexity.

---

# Before You Start

Before writing code:

- Read the project README.
- Review the relevant documentation in the `docs/` directory.
- Check existing ADRs for previous architectural decisions.
- Search for existing issues or discussions related to your change.

If your work changes the architecture, create or update an ADR before implementation.

---

# Development Environment

IdentityCore is developed using Ubuntu and Docker.

Required software:

- Git
- Docker
- Docker Compose
- Python
- Node.js
- PostgreSQL (if running without Docker)
- Redis (if running without Docker)

Follow the setup instructions in the project README.

---

# Branch Naming

Use descriptive branch names.

Examples:

```text
feature/verification-sessions
feature/manual-review
feature/provider-adapters

fix/tenant-filter
fix/webhook-retry

security/api-key-rotation

docs/api-spec

chore/docker-update
```

Avoid generic branch names such as:

```text
test
new
update
work
branch1
```

---

# Commit Messages

Follow the Conventional Commits format.

Examples:

```text
feat: add verification session service
fix: enforce tenant isolation on verification lookup
docs: update deployment guide
refactor: simplify webhook delivery service
test: add face match integration tests
security: encrypt biometric templates
chore: update dependencies
```

Commit messages should describe **what changed**, not the entire implementation.

---

# Pull Requests

Every pull request should include:

- A clear description of the change.
- The reason for the change.
- Any related issue or ADR.
- Testing performed.
- Documentation updates, if applicable.
- Security considerations for security-sensitive changes.

Keep pull requests focused. Avoid combining unrelated features into one pull request.

---

# Coding Standards

All contributions must follow the project's Coding Standards document.

Key principles include:

- Clear, readable code.
- Type hints where practical.
- Small, focused functions.
- Business logic in the service layer.
- Tenant-aware database queries.
- No hardcoded secrets.
- No unnecessary dependencies.

---

# Security Requirements

Security is mandatory.

Every contribution should:

- Validate user input.
- Enforce authorization.
- Respect tenant isolation.
- Protect sensitive information.
- Avoid exposing internal identifiers.
- Prevent logging of secrets or biometric data.

If a change introduces a new security risk, document it and discuss it before merging.

---

# Testing Requirements

New features should include appropriate tests.

Depending on the feature, this may include:

- Unit tests
- Integration tests
- API tests
- End-to-end tests

Bug fixes should include regression tests whenever practical.

Code that cannot be tested should include a clear explanation.

---

# Documentation

Update documentation whenever changes affect:

- APIs
- Database schema
- Business logic
- Security behavior
- Deployment
- Configuration
- User workflows

Documentation should remain synchronized with the implementation.

---

# Architecture Decisions

Significant architectural changes should be documented using an Architecture Decision Record (ADR).

Examples include:

- Changing the database strategy.
- Introducing a new AI model.
- Adding a new provider architecture.
- Modifying tenant isolation.
- Changing authentication methods.

---

# Dependencies

Before adding a new dependency, consider:

- Is it actively maintained?
- Is it secure?
- Is it necessary?
- Can the functionality be implemented using existing libraries?

Prefer fewer, well-maintained dependencies over many small packages.

---

# Performance

Contributors should consider:

- Database query efficiency.
- API response times.
- Background task performance.
- Memory usage.
- Scalability.

Avoid premature optimization, but do not ignore obvious performance issues.

---

# AI Contributions

Changes to the AI service should:

- Record model versions.
- Preserve existing API contracts.
- Return confidence scores.
- Avoid making business decisions.
- Support rollback to previous models.

New AI models should be evaluated before replacing existing ones.

---

# Security Reporting

If you discover a security vulnerability:

- Do **not** create a public issue.
- Report it privately to the maintainers.
- Include reproduction steps where possible.
- Allow time for investigation and remediation before public disclosure.

---

# Development Philosophy

IdentityCore values:

- Simplicity over cleverness.
- Explicit behavior over hidden magic.
- Security over convenience.
- Maintainability over short-term speed.
- Correctness over premature optimization.

Every contribution should leave the codebase better than it was found.

---

# Definition of Done

A contribution is considered complete when:

- The implementation works correctly.
- Tests pass.
- Relevant documentation is updated.
- Coding standards are followed.
- Security requirements are satisfied.
- No existing functionality is broken.
- The code is ready for production review.

---

# Thank You

Thank you for contributing to IdentityCore.

Every improvement—whether a new feature, a bug fix, better documentation, or a security enhancement—helps build a trustworthy identity verification platform that organizations can confidently rely on.
