# Verification reviewer permissions

Apply the data migration `access_control.0007` in a planned maintenance window before deploying the permission boundary. It is not an automatic rolling-schema expansion; the rollout migration guard must continue rejecting generic data migrations. Inventory custom reviewer roles first, grant the permission to intended roles, then resume review traffic. Tenant
membership is no longer sufficient to list manual review, inspect review evidence,
claim/decide/check a case, allocate a queue, or access independent quality review.
An active, nondeleted tenant role must grant `review_verification`; its membership,
user and case must belong to the same tenant. Suspended/deleted users or roles deny
access. Role revocation is rechecked during manual decision finalization.

The migration grants this permission only to built-in **system** Tenant Administrator,
Organization Administrator and Verification Officer roles. Existing custom roles do
not acquire it merely because of their names or because they were queue members.
An accountable organization administrator must explicitly grant it to the intended
custom reviewer role before restoring that team's review access. New onboarding
administrators and the local seed receive it through normal role setup. Queue
configuration additionally requires `manage_team`.

Platform administrators continue to review platform-owned onboarding cases; they
cannot use platform authority to decide tenant-owned cases. Assignment, skills,
availability, maker-checker, creator/applicant exclusions and terminal-state checks
remain mandatory after the role check. A role permission is not an override for them.

Validate positive and negative access through REST and internal GraphQL after rollout.
A normal unprivileged member must not see case/QA/evidence metadata or create a decision.
Authorized reviewers must still complete normal and independent review journeys.
Do not reintroduce tenant-membership fallback to avoid updating a custom role.

This control does not implement general verification-case escalation. Organization
onboarding escalation is a separate platform workflow.
