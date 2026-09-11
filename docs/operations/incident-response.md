# Incident response and breach triage

Owner: Security lead. Review at least every six months and after every SEV1/SEV2
incident. This runbook defines repository procedures; a deployment is not ready
until its private contact roster and exercise evidence are complete.

Use this runbook for suspected unauthorized access, credential exposure, tenant
isolation failures, consent or retention failures, unreliable decisions, outages,
and suspected loss or disclosure of identity or biometric evidence. A credible
report starts triage even when monitoring is unavailable. IC-087 supplies the
observability integration; its completion is still a separate dependency.

## Declare and assign

1. Create an incident record in the organization's restricted incident system.
   Assign an incident ID and record UTC detection time, reporter, affected
   environment, known symptoms, and the source of the report. Put references in
   the record; do not paste credentials, identities, documents, or biometric data.
2. Page the on-call service owner and security lead using the private roster.
   Assign a commander, technical lead, security/privacy lead, communications
   owner, and scribe. A small team may combine roles, but the technical operator
   must not be the only approver of evidence disclosure or destructive recovery.
3. Open a restricted incident channel and a separate sanitized status thread.
   Confirm who owns the next action, the next update time, and the escalation
   route. Record every handoff; the outgoing owner remains responsible until
   the incoming owner explicitly accepts.
4. Classify severity using the highest applicable row. Unknown disclosure scope
   is treated as suspected disclosure until security/privacy documents otherwise.

| Severity | Trigger | Initial response and update target |
| --- | --- | --- |
| SEV1 | Suspected cross-tenant disclosure, active credential abuse, biometric/document exposure, widespread integrity failure, or production unavailability with no safe workaround | Page immediately; target acknowledgement within 15 minutes; updates every 30 minutes |
| SEV2 | Material tenant/service degradation, stalled processing or delivery, suspected limited security incident, or lost redundancy threatening recovery | Page immediately; target acknowledgement within 30 minutes; updates hourly |
| SEV3 | Contained defect with a safe workaround, no indication of unauthorized access, and no imminent data loss | Assign an owner within one business day; update daily until contained |

These are internal response targets, not contractual SLOs or notification
periods. If acknowledgement misses its target, escalate to the secondary and
engineering lead; do not wait for the next scheduled update. The commander may
raise severity immediately. Downgrades require a recorded rationale and agreement
from security/privacy when data exposure or integrity is implicated.

## Private contact roster

The deployment owner maintains a restricted, independently accessible on-call
roster in the organization's incident system and an approved offline fallback.
The deployment handover must name its exact location and verify access from a
responder account. Do not put personal phone numbers or credentials in GitHub.

| Role | Required roster entry | Fallback |
| --- | --- | --- |
| Incident commander | Primary and secondary on-call engineering leads and paging routes | Executive incident sponsor |
| Technical response | API/worker, AI/provider, database/storage, and frontend owners | Engineering lead assigns a qualified deputy |
| Security/privacy | Security lead and privacy decision owner | Executive sponsor secures qualified coverage |
| Communications | Customer communications owner and approver | Commander assigns a deputy |
| External dependencies | Cloud/storage/provider support portal, account reference, escalation route | Procurement/vendor relationship owner |
| Affected organizations | Verified contractual security/incident contact per tenant | Account owner verifies an alternate through an independent channel |

Before a pilot, fill every entry, test primary/secondary reachability, and record
who tested it and when. Missing contacts or inaccessible fallback routes block
operational readiness. Never trust replacement bank, email, or support contacts
provided only through the suspected compromised channel.

## Triage, containment, and recovery

The technical lead records facts separately from hypotheses: affected versions,
environments, tenants, time window, entry point, provider/storage region, decision
or delivery integrity, and whether access may still be active. Use authorized,
tenant-scoped queries. An absence of logs is not evidence that no disclosure
occurred. Preserve evidence using [the evidence procedure](incident-evidence.md)
before changing affected systems when that does not prolong active harm.

| Scenario | Immediate containment | Recovery evidence |
| --- | --- | --- |
| Credential/session exposure | Disable affected credential or session issuance and revoke implicated material using the approved administrative path; rotate dependent secrets from a clean responder environment | Old credentials fail, replacements work only for intended scopes, and unauthorized activity stops |
| Tenant isolation or evidence disclosure | Disable the affected access path or feature; stop new exposed operations; restrict implicated provider/storage access | Regression reproducer is fixed; owner and non-owner access are tested in every affected environment |
| Provider/biometric integrity | Stop unsafe automated decisions; use only an approved fallback or manual-review route | Provider checks, terminal decisions, and manual-review ownership reconcile; no blind bulk reprocessing |
| Queue/webhook outage | Contain the failing dependency and preserve pending records; recover with the existing idempotent recovery runbooks | Backlog drains and stable event IDs remain intact; receivers atomically deduplicate by event ID so retries do not produce duplicate side effects |
| Consent failure | Stop affected collection and processing with the responsible owner; establish approved preservation scope | Purpose/version boundaries are verified before processing resumes |
| Premature or erroneous deletion | Pause the affected deletion path and preserve the approved scope | Correct retention policy and recovery are verified before deletion resumes |
| Overdue or failed deletion | Stop affected collection or other processing as required; continue approved deletion remediation outside a valid preservation hold | Expired data is demonstrably deleted, failed operations are retried, and retention boundaries are restored |
| Deployment regression | Halt rollout and decide whether an approved compatible rollback is safer than a forward fix | Health plus representative tenant-scoped journeys pass; data/schema compatibility is demonstrated |

Use [processing recovery](processing-job-recovery.md),
[processing ownership](processing-job-ownership.md), and
[provider route resilience](provider-route-resilience.md) for their supported
procedures. This runbook does not authorize deleting production records,
bypassing terminal decisions, restoring over production, or opening evidence
storage to broad access. Record the operator, approver, scope, rollback plan,
and result before and after a consequential containment/recovery operation.

## Notification decision

The communications owner prepares a factual draft; the security/privacy owner
assesses disclosure and the applicable contractual/regulatory obligations with
qualified counsel. Record each affected organization/jurisdiction, the time the
relevant obligation was assessed to start, its basis, deadline, recipient,
approver, and delivery evidence in the private decision log. Do not assume one
universal deadline. Lack of complete scope must not silently postpone assessment.

Decide separately about internal leadership, affected organizations, providers,
regulators, and individuals. Record an explicit notify / defer / not-required
decision for each category with rationale, owner, and reassessment time. A
notification draft states what is confirmed, what remains unknown, time window,
affected service/data categories, containment, requested recipient actions, and
the next update. Never attach raw evidence or an unverified list of subjects.
Verify recipient identity and channel independently before sending. Sending is
an authorized human communications action, not an automatic runbook step.

Use the [incident record template](incident-record-template.md) for decisions,
evidence references, handoffs, and notification tracking.

## Resolve and learn

The commander declares resolution only after the technical lead demonstrates
service recovery, security/privacy agrees that active harm is contained, and
the communications owner has addressed outstanding updates. Distinguish service
restoration from final investigation and notification closure. Record residual
risk, monitoring owner, next review time, and any approved temporary controls.

Hold a blameless review within five business days for SEV1/SEV2. Capture root and
contributing causes, detection gaps, affected scope, what worked, and corrective
issues with priority, owner, due date, and verification evidence. Track unfinished
notification, retention-hold, and deletion obligations to their owners rather than
closing them with the incident. Update runbooks and exercise scenarios after
material findings.

## Exercises and acceptance evidence

Run credential-exposure and provider-outage tabletop exercises before the first
pilot and at least twice yearly. Add a tenant-isolation/evidence-preservation
scenario annually and after material access-control changes. Use synthetic
records in an isolated environment and a simulated communications channel.
Never exercise by exposing real customer data or contacting real recipients.

The facilitator injects an unavailable primary contact, missing telemetry, a
suspected cross-tenant impact, and a notification decision under incomplete
information. Responders must demonstrate secondary escalation, explicit role
handoff, UTC decision logging, tenant-scoped evidence custody, containment
approval, recovery checks, and an approved simulated notification.

Pass only when every step has an owner and timestamp, evidence hashes validate,
no synthetic sensitive payload reaches public logs, and every gap has a tracked
corrective action. The security lead records pass/fail with an evidence reference;
critical gaps require a repeat exercise before pilot approval. A checked-in
runbook is not proof that an exercise has occurred.
