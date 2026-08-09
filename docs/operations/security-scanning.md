# Security scanning

IdentityCore runs automated security scans on every push and pull request, on manual
request, and weekly. The `Security` workflow covers:

- dependency lockfiles across the repository;
- secrets in the checked-out source tree; and
- the Django, managed-AI, and verification-portal runtime images.

## Enforcement policy

High and critical dependency or container findings with an available fix fail the
workflow. Any detected secret fails the workflow. Lower-severity and currently
unfixed vulnerability findings remain visible in the generated artifacts for triage.

The workflow uploads JSON reports for 30 days even when an enforcement step fails.
Reports must be treated as security-sensitive because scanner context can include file
paths and dependency details. Do not copy a detected secret into an issue or pull
request; revoke it first and use a redacted reference.

## Triage and exceptions

1. Confirm the package, image layer, affected version, and reachable code path.
2. Upgrade or remove the affected dependency and regenerate its canonical lockfile.
3. Rebuild and rerun the relevant test and security jobs.
4. For a false positive or an unavoidable finding, document the advisory, owner,
   compensating control, and an expiry date in a dedicated security issue before adding
   a narrowly scoped scanner exception.

Exceptions must never contain credentials, personal data, document images, or biometric
data. Expired exceptions block delivery until they are removed or explicitly renewed.

## Local checks

Frontend dependency advisories can be checked from `frontend/` with:

```bash
pnpm audit --audit-level high
```

The CI workflow is authoritative because it also scans all supported dependency
manifests, the source tree for secrets, and the built runtime images.
