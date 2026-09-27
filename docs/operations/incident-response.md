# Incident response and breach triage

Last reviewed: 2026-09-27

This runbook covers suspected security, privacy, availability, integrity, and
provider incidents affecting IdentityCore or its tenants. Use the incident
record as the authoritative timeline and decision log. Do not put secrets,
personal data, identity documents, consent content, or biometric data in the
record, chat, tickets, or screenshots.

## Before an incident

The on-call owner maintains the contact directory in the organization’s access
controlled incident system. Keep named contacts and phone numbers there rather
than in this repository. Verify the directory and escalation paths quarterly
and after role changes.

| Role | Responsibility | Primary contact location |
| --- | --- | --- |
| Incident commander | Sets severity, assigns owners, coordinates response, and records decisions | On-call directory |
| Security lead | Leads containment, credential handling, and technical investigation | On-call directory |
| Privacy lead | Assesses personal-data impact, retention, and notification obligations | On-call directory |
| Service owner | Restores service, evaluates rollback, and coordinates engineering | On-call directory |
| Communications owner | Prepares approved internal and external updates | On-call directory |
| Legal counsel | Advises on contractual and regulatory obligations | On-call directory |
| Tenant contact owner | Coordinates affected-tenant communications through approved channels | On-call directory |

One person may hold multiple roles for a small response, but the incident
commander must explicitly assign each responsibility. Escalate to the backup
contact if an owner does not acknowledge the page within the organization’s
documented on-call response target.

## Severity and escalation

The incident commander sets the initial severity and records the rationale.
Increase severity when the scope or impact is uncertain; lower it only after
evidence supports the change.

| Severity | Examples | Response |
| --- | --- | --- |
| SEV-1 | Confirmed unauthorized disclosure of highly sensitive data; active compromise of signing or encryption keys; tenant isolation failure; broad loss of verification integrity | Page security, privacy, service owner, and legal immediately; stop affected processing or access; executive escalation |
| SEV-2 | Suspected sensitive-data exposure with scope unknown; sustained major outage; provider compromise or widespread incorrect decisions | Page security and service owner immediately; engage privacy and legal while triaging; consider tenant-specific pause |
| SEV-3 | Limited degradation or contained security event with no known sensitive-data impact | Assign an incident owner during the current support period; investigate and monitor |
| SEV-4 | Low-impact defect or near miss with no service or data impact | Track to resolution in the normal engineering workflow |

Any suspected personal-data breach is escalated to the privacy lead and legal
counsel regardless of severity. The privacy lead and counsel determine whether,
when, and to whom notices are required. Do not infer a notification deadline
from this runbook or send a notice before approval.

## Response sequence

1. **Open the incident.** Create a record with an opaque incident ID, reporter,
   discovery time, affected service/environment, summary, initial severity, and
   commander. Record links to restricted evidence locations, not evidence itself.
2. **Assign roles and establish a channel.** Use an access-controlled channel.
   Record the communications owner and the next update time. Avoid copying
   personal or verification data into chat.
3. **Contain safely.** Prefer reversible, narrowly scoped controls: revoke
   exposed credentials, disable affected routes or providers, pause new sessions
   for the affected tenant/environment, open a provider circuit, or roll back
   the deployment. Preserve already completed workflow steps and avoid replaying
   evidence submissions or decisions.
4. **Preserve evidence.** Follow the evidence handling procedure below before
   cleanup or rotation when that does not extend active exposure. Containment
   takes priority when delay would increase harm.
5. **Establish scope and impact.** Use request/correlation IDs, timestamps,
   route templates, deployment versions, provider-check IDs, and tenant-scoped
   audit records. Determine affected time range, environments, tenants, data
   classes, workflow integrity, and whether access or exfiltration is evidenced.
6. **Decide on notification.** The privacy lead and counsel evaluate applicable
   legal, contractual, regulator, and tenant obligations using verified facts.
   The communications owner prepares notices; authorized owners approve and
   send them through the approved contact directory and channels. Record the
   decision and rationale, including a decision not to notify.
7. **Recover and monitor.** The service owner verifies the fix, data integrity,
   tenant isolation, queues, provider health, and affected workflows before
   resuming processing. Use a staged rollout and watch the relevant alerts.
8. **Close and learn.** The commander confirms owners and due dates for follow-up
   work, then schedules a blameless review. Do not close an incident while
   notification decisions or evidence custody remain unassigned.

## Evidence preservation and decision log

- Preserve only the minimum evidence needed to answer the incident questions.
- Store exports, snapshots, and provider correspondence in the approved
  restricted evidence location with encryption and access logging.
- Record who collected or accessed an artifact, when, why, its source, a
  cryptographic checksum where appropriate, and any transfer or transformation.
- Preserve relevant audit events, deployment/configuration versions, access
  logs, and provider incident identifiers. Keep original timestamps and note
  clock uncertainty.
- Never export raw identity documents, selfie/video captures, biometric
  templates, session tokens, bearer cookies, API secrets, signed upload URLs,
  or unredacted request/response bodies into an incident record. If direct
  examination of highly sensitive data is necessary, the privacy and security
  leads approve a time-limited, least-privilege procedure in the restricted
  evidence system.
- Preserve relevant logs before retention expiry. Do not disable audit logging
  or alter production records to simplify investigation.
- Record each material decision with timestamp (UTC), decision owner, options
  considered, evidence references, rationale, and follow-up owner. Keep
  notification decisions and approvals in the same log.

## Incident record template

Use the approved incident system and include:

- Incident ID, severity, status, commander, role assignments, and timestamps.
- Affected services, environments, tenant IDs, deployment versions, and data
  classes. Do not include applicant names or evidence payloads.
- Detection source, known facts, open questions, and confidence level.
- Containment, recovery, rollback, and validation actions with owners and times.
- Restricted evidence references and custody history.
- Impact and notification assessment, decision owners, approvals, and rationale.
- Stakeholder update times and approved message references.
- Corrective actions, accountable owners, due dates, exercise/review date, and
  closure approval.

## Scenario playbooks

### Credential or token exposure

Revoke the affected credential/session family, disable issuance if necessary,
rotate implicated signing material through the approved key-rotation process,
and inspect access logs using request IDs. Check whether other tenants or
environments share the affected credential. Do not paste the credential into a
ticket, shell history, or chat. Validate revocation and resumed issuance with a
synthetic request.

### Biometric or identity-evidence/provider incident

Pause the affected provider route and automatic adverse decisions. Use an
approved fallback or manual review if its policy permits. Preserve provider
check IDs, contract/version, timestamps, and decision metadata without copying
payloads. Confirm evidence access, retention/deletion controls, replay status,
and whether decisions need reprocessing or correction before resuming.

### Tenant isolation or unauthorized access

Disable the affected access path, preserve authorization and audit events, and
identify the boundary, time range, and potentially reachable tenant resources.
Validate isolation with separate synthetic tenants before restoration. The
privacy lead and counsel assess tenant notification with verified scope.

### Availability or data-integrity incident

Use the relevant service recovery and provider resilience runbooks. Stop
operations that may duplicate uploads, decisions, or webhook side effects.
Check queue ownership, idempotency, audit continuity, and database/object
consistency before replay or restore. Record recovery-point and recovery-time
observations for follow-up.

### Consent or configuration mismatch

Pause new sessions for the affected tenant, locale, environment, or consent
version. Preserve the published configuration version and acceptance metadata.
Have privacy/legal owners decide whether existing sessions may continue or
require renewed consent; do not rewrite historical consent records.

## Exercises and post-incident review

Before a pilot, exercise credential exposure and provider outage scenarios with
synthetic data in a non-production environment. Repeat at least annually and
after a major response-process change. Record participants by role, scenario,
timings, missed escalations, containment and recovery results, and corrective
actions. Never use production applicant evidence for an exercise.

Within five business days after closure, hold a blameless review unless the
commander records a reason to schedule it later. Review detection, impact,
containment, notification decisions, evidence handling, recovery, and whether
existing controls worked. Assign every action an owner and due date, and track
actions to verified completion.
