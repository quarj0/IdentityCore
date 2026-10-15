# Release evidence integrity gate

This is a local **fail-closed structural and file-integrity gate**. It is NOT
biometric validation, an independent penetration test, legal approval, signature
verification, or authorization to process live identity data. The tool checks
completeness, scope, recency, SHA-256 integrity and different owner/reviewer
names for independent review categories. An untrusted or fabricated manifest
may still pass: the accountable release owner MUST separately authenticate
reviewers and verify evidence provenance in restricted change management.

Do not commit applicant data, documents, consented evaluation datasets,
biometric templates, credentials, sensitive results or approval records to GitHub.

## Release prerequisites

Every combined BYOP + managed-verification pilot requires actual evidence for:
historical review remediation; real-world managed model evaluation using locked
representative cohorts; a live external BYOP provider journey with failover;
deployed API security and readiness probes; actual database and object-store
backup/restore; load testing using REAL model inference (not the CI synthetic
AI latency fixture); live on-call alert delivery; an independent security
assessment; privacy and legal approval; and a named go-live decision.

Commercial release additionally requires billing/payment reconciliation evidence
and approved commercial terms. Billing work or a green CI build alone cannot
satisfy either requirement.

## Invocation (restricted operator machine)

Provide a private manifest and hashed, sanitized evidence files outside GitHub:

    python scripts/check_release_evidence.py \
      --manifest /private/identitycore-release/manifest.json \
      --evidence-root /private/identitycore-release/artifacts \
      --head-sha "$(git rev-parse HEAD)" \
      --mode pilot

Use --mode commercial only when all commercial prerequisites are approved.
The exit code is nonzero if any requirement fails. Match the head SHA to the
EXACT release commit; do not bypass the gate with an older evaluation.

Manifest has schema_version=1, environment="production", mode="pilot" or
"commercial", head_sha=<40-digit lowercase hex commit>, and a checks object
with exactly the keys defined in COMMON/COMMERCIAL in the Python module.
Every check object must have result="pass", owner, reviewer, completed_at
(UTC ISO-8601), and artifacts: at least one {path, sha256} with a sanitized
relative path under the private evidence root. Every SHA-256 must be hex.
Independent checks require a reviewer different from the check owner.
Stale and future-dated evidence is rejected.

The presence of an integrity-valid file does not certify its claims. A
synthetic file with matching hash is ONLY suitable for unit tests, never
release signoff. Real approvals must remain in the external restricted
change system and be verified by human owners.

Run unit tests:

    python -m unittest discover -s tools/evaluation -p test_release_evidence_gate.py

See pilot-readiness-checklist.md, locked-evaluation.md,
provider-setup.md, deployment-security.md, and backup-restore.md.
