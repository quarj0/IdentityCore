# Independent review quality

Access requires an active tenant role granting `review_verification`; management actions additionally require `manage_team`. See [reviewer permission rollout](reviewer-permissions.md).

Set `sampling_percent` (0–100, default 0) when creating or editing a tenant review queue. Sampling applies to future completed manual decisions in that queue's environment. A server-keyed hash of verification and decision revision selects samples deterministically. A maker-checker proposal is sampled only after approval. Each sampled revision freezes the sampling percentage, original final outcome/codes, required skills and original reviewers.

The service assigns available qualified reviewers by pending QA workload, oldest assignment timestamp and stable user ID. The maker, checker, applicant and case creator are excluded. If no reviewer qualifies, the sample stays unassigned. Add available qualified queue members, then an independent queue manager can allocate it. Keep at least one qualified reviewer separate from the maker and checker.

Session-authenticated internal routes under `/api/v1/verifications` use `environment=sandbox|production` (default sandbox):

- `GET /review-quality?pending=true`: assigned samples, or management-visible samples. All responses exclude samples made or checked by the current user, including managers.
- `GET /review-quality/{id}`: workflow and outcome summary; original reviewers receive 404.
- `POST /review-quality/{id}`: the assigned eligible reviewer submits `outcome` (`verified`, `rejected`, `failed`), `reason_code`, and optional `notes`. The immutable policy's reason catalog and plain-text note requirements apply. Notes are encrypted and never appear in reports or list/detail responses. Identical repeated submissions are idempotent; differing repeats fail.
- `POST /review-quality/{id}/allocate`: independent managers who are available queue members allocate an unstaffed sample fairly. The chosen reviewer may be another eligible member.
- `GET /review-quality/report`: `manage_team` managers receive sampled/pending/completed counts, agreement/disagreement counts and an outcome cross-tab, excluding their own maker/checker samples. Counts are therefore scoped to each manager's permitted population.

The dashboard Manual review page shows pending independent QA assignments, environment selection and authorized aggregate reports. Recording quality assessments does not modify verification outcomes, applicant results, evidence reports or verification webhooks. Reports contain no biometric media, capture URLs, applicant contact details or reviewer notes. A disagreement is evidence for a subsequent separately authorized investigation, not an automatic applicant decision reversal.
