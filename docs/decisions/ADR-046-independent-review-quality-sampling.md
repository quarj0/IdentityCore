# ADR 046: Independent review quality sampling

Status: Accepted

Tenant environment queues configure a percentage of completed manual decisions for quality review. A purpose-separated server-keyed hash of tenant, verification and decision revision chooses samples deterministically. Sampling configuration and final decision codes are frozen per revision; retries cannot create extra samples. Sampling runs in the final-decision transaction, including maker-checker approval, so it cannot observe an unapproved proposal.

Quality assignments exclude the original maker, checker, case creator and applicant. Available queue reviewers with the frozen skills receive the least-loaded assignment, with last-assignment time and stable user ID as tie breakers. Unstaffed samples remain pending until eligible staff allocate them. Original reviewers cannot list or inspect their own QA assignment, including through management/report APIs.

Quality reviews record a separate outcome and reason without changing the applicant's final verification result or its webhooks. QA APIs provide IDs, bounded machine reason codes and outcome summaries rather than document images, capture links, or biometric payloads. Reports aggregate agreement and disagreement by environment and outcome, with original-reviewer exclusions enforced before aggregation. Configuration and QA decisions are audited.
