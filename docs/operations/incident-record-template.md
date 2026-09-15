# Restricted incident record template

Copy this template into the approved private incident system. Do not commit
filled incident records to the repository. Use UTC timestamps and distinguish
confirmed observations from hypotheses. Use restricted evidence references
instead of sensitive payloads.

## Declaration and ownership

- Incident ID / title:
- Detection time / report source / declaration time:
- Severity / rationale / next reassessment:
- Environment / affected service / deployment version:
- Commander / technical lead / security/privacy lead / communications owner / scribe:
- Private channel / sanitized status thread / next update:
- Contact roster location / primary and fallback reachability verified at:
- Current confirmed scope / unknown scope / investigative hypotheses:

## Timeline, decisions, and handoffs

| UTC time | Observation or decision | Basis / uncertainty | Operator / approver | Scope / rollback | Result / evidence reference | Next action / owner / due time |
| --- | --- | --- | --- | --- | --- | --- |

For each role handoff, record outgoing/incoming owners and explicit acceptance.
For each severity change or deferred action, include the rationale and next review.

## Evidence and preservation

| Artifact ID | Source tenant/environment | Acquisition UTC / collector / authority | Restricted location | Bytes / SHA-256 | Original or redacted derivative | Retention/hold owner and review date |
| --- | --- | --- | --- | --- | --- | --- |

| Transfer UTC | Artifact ID | Sender / recipient / authorization | Purpose | Source/destination references | Hash verified before/after |
| --- | --- | --- | --- | --- | --- |

- Audit-chain verification result / snapshot time / missing intervals:
- Database, object lifecycle, provider, and backup preservation acknowledgements:
- Evidence access log reference / integrity limitations:

## Notification assessment

| Recipient category / organization | Notify / defer / not required | Confirmed facts and rationale | Obligation basis / assessed start / deadline | Owner / approver | Verified channel / draft reference | Sent UTC / delivery proof / next reassessment |
| --- | --- | --- | --- | --- | --- | --- |

Track internal leadership, organizations, providers, regulators, and individuals
separately. Use qualified privacy/legal assessment for applicable obligations.

## Restoration, closure, and review

- Containment actions and approval references:
- Recovery tests / tenant-environment access checks / residual risks:
- Service restored at / approved by / follow-up monitoring owner:
- Outstanding investigation and notification tasks:
- Post-incident review date / facilitator / root and contributing causes:
- Corrective issues with priority, owner, due date, and acceptance evidence:
- Hold release / deletion verification / failures requiring retry:
- Final investigation closure at / security-privacy approval / communications completion:

## Exercise record (when simulated)

- Scenario / facilitator / participants / isolated environment:
- Inject times and response times / escalation and handoff evidence:
- Synthetic evidence integrity and access checks:
- Simulated notification approval and delivery:
- Pass/fail / gaps and corrective issues / repeat date / security lead sign-off:
