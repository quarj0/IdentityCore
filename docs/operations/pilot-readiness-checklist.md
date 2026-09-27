# Pilot onboarding and go-live checklist

Use one copy for each organization and environment. Complete it in the approved change or readiness system so the final approval and evidence links are access controlled and timestamped. Do not place credentials, applicant data, identity documents, consent text, or biometric evidence in the checklist.

## Record

- Organization ID:
- Environment and region:
- Planned go-live date/time (UTC):
- Checklist version: `1.0`
- Checklist owner:
- Security reviewer:
- Privacy reviewer:
- Service owner:
- Change or approval record URL:
- Configuration/deployment version:

For each item record **status** (pass, fail, not applicable), **owner**, **checked at (UTC)**, and a restricted evidence or ticket reference. A not-applicable item needs a rationale. Any failed item blocks approval unless the accountable security/privacy owner documents an approved exception and expiry in the change record.

## Security

- [ ] Tenant membership, roles, and least-privilege access are verified using the target environment.
- [ ] Tenant isolation is checked across API, storage, queues, audit events, and support access.
- [ ] Secrets are stored in the approved secret manager, rotated for the environment, and absent from browser bundles and logs.
- [ ] TLS, secure cookies, CSRF/origin checks, rate limits, and request-size limits are enabled.
- [ ] Audit events are enabled and access-tested; request IDs can correlate support events without including payloads.
- [ ] Incident contacts, escalation route, and the incident runbook have been reviewed and exercised.

## Privacy, consent, and retention

- [ ] The processing purpose, data categories, lawful basis, tenant instructions, and privacy contact are recorded.
- [ ] Consent text, version, and locale match the approved tenant configuration; consent capture is verified in a synthetic session.
- [ ] Evidence retention and deletion periods are approved for each evidence class and configured for this environment.
- [ ] Deletion, legal hold, and tenant offboarding procedures have an accountable owner and have been verified.
- [ ] Support and analytics views exclude raw evidence and direct identifiers; access is limited to the required roles.

## Providers and workflow

- [ ] Required identity and biometric providers are configured for the correct tenant/environment and their credentials have been validated.
- [ ] Provider contracts, permitted data use, retention, regions, and subprocessors are approved.
- [ ] Provider health, timeout, retry, circuit-breaker, fallback, and manual-review routes are verified with synthetic fixtures.
- [ ] Webhook endpoints, signatures, retries, replay handling, and delivery visibility are verified without using applicant data.
- [ ] Workflow steps, decision thresholds, review routing, supported locales, and applicant handoff paths match the approved configuration.

## Limits and operational controls

- [ ] Tenant quotas, upload limits, session expiry, rate limits, and concurrency limits are agreed and configured.
- [ ] Monitoring and alerts cover availability, completion, failure, latency, provider health, queue age, and security events.
- [ ] Dashboards and alerts use aggregate or pseudonymous operational dimensions and do not expose small cohorts or payloads.
- [ ] Backup, restore, rollback, and data-integrity checks are available for this environment.
- [ ] Capacity and provider limits have been checked against the pilot volume and ramp plan.

## Contacts and rollback

- [ ] Tenant operational, privacy, security, and escalation contacts are verified in the restricted contact directory.
- [ ] IdentityCore on-call, provider escalation, and incident commander contacts are current.
- [ ] Rollback trigger, decision owner, command/procedure, expected duration, and post-rollback validation are recorded.
- [ ] A stop-processing procedure is ready for consent mismatch, tenant isolation risk, provider compromise, or evidence integrity failure.
- [ ] Pilot cohort, support hours, communication channel, and staged traffic ramp are documented.

## Approval

Approval is recorded in the linked change system, not by editing this template alone. The record must capture:

- Organization ID, environment, checklist version, and configuration/deployment version.
- Status of every check, named accountable owner, UTC completion timestamp, and restricted evidence reference.
- Open risks, exceptions, compensating controls, expiry, and the owner accepting each risk.
- Security, privacy, and service-owner decisions with UTC timestamp and rationale.
- Final go/no-go decision, approver, UTC timestamp, planned start, and rollback authority.

No unresolved critical security, privacy, consent, tenant-isolation, deletion, or recovery check may be waived for a pilot. After go-live, retain the completed record under the change-management retention policy and attach a dated review after the first pilot cohort.
