# ADR 045: Tenant review queues and fair assignment

Status: Accepted

Tenant administrators configure environment-scoped queues with priority, SLA, document-country filters and required skills. Queue membership stores administrator-approved reviewer skills and availability. Applicant metadata cannot supply country or skills. Unknown document country matches only unrestricted queues. Platform onboarding keeps its independent ownership boundary.

Queue entries freeze priority, deadline and required skills when admitted. Admission and assignment serialize on the tenant audit lock before locking cases. Among eligible reviewers, assignment chooses the smallest active workload, then oldest last-assignment time and stable user ID. The case creator and applicant cannot receive their own case. Existing assignments are never overwritten. The same locking order applies to review decisions and approvals.

Configuration and assignments are audited. Queue APIs return workflow metadata; they do not add document images or biometric evidence. Existing tenants without configured queues retain their current manual-review workflow. Queue configuration uses internal authenticated APIs and explicit manage_team permission; API clients cannot administer reviewer capabilities.
