# Tenant review queues

Queue configuration uses authenticated dashboard sessions and the `manage_team` role permission. API credentials cannot administer reviewer skills. Routes are internal under `/api/v1/verifications`:

- `GET/POST /review-queues`: list or create tenant queues. Creation accepts `name`, `environment` (`sandbox` or `production`), `priority` (0–1000), `sla_minutes` (1–43200), `country_codes` (unique uppercase two-letter codes), `required_skills` (unique lowercase machine codes), and `active`.
- `PATCH /review-queues/{queue_id}`: edit configuration. Environment cannot change. Deactivate a queue to pause assignments; entries keep their original priority, deadline and skill requirements.
- `GET/PUT /review-queues/{queue_id}/members`: managers inspect or update a member using `user_id`, `skills`, and `available`. Only active users belonging to this tenant can be members.
- `GET /review-queues/{queue_id}/cases`: members and managers inspect queue workflow metadata. Optional `country`, `skill`, `overdue=true|false`, `page`, and `page_size` filters apply. No documents, biometrics or applicant contact details appear in these responses.
- `POST /review-queues/{queue_id}/cases`: available members allocate the next eligible case. The returned assignment can belong to another reviewer. It is selected by active workload within the same environment, then oldest last-assignment time and stable reviewer ID. This endpoint allocates work; it is not a self-claim operation.

For example, create a sandbox queue with `{"name":"Passport specialists","environment":"sandbox","priority":100,"sla_minutes":30,"country_codes":["GH"],"required_skills":["passport"]}`, then add reviewers with matching approved skills. The dashboard Manual review page lists configured queues, displays priority and overdue deadlines, filters country and skill, and allocates the next case.

Admission uses document classifier output; applicant metadata cannot select a country queue. Unknown countries match only unrestricted queues, so configure an unrestricted fallback. Higher priority queues take precedence, followed by stable creation order. Admission freezes configuration; edits affect future entries. New manual-review transitions record their start time. Cases predating that field conservatively use case creation time for SLA calculation.

Configured queues require assignment before a reviewer may submit a decision; the reviewer must still be available and satisfy the frozen skills. Disable availability to pause a reviewer. The creator and applicant cannot receive their own case. Platform onboarding remains in its separate platform review queue. Without tenant queues, existing manual review behavior is preserved. Configuration changes and assignments append audit events.
