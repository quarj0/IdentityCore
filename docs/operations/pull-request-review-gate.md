# Pull-request review gate

Before merging a pull request:

1. Review the complete change and request the configured GitHub review. Wait for the review to finish; an empty thread list while a review is running is not completion.
2. Reproduce each substantive finding against the current code. Fix valid findings with an appropriate regression or explain why the finding is superseded or inapplicable, linking current code and validation.
3. Reply to each original review thread with the fixing commit and evidence. Resolve a thread only after that evidence exists. Never infer correctness from GitHub's resolved flag.
4. After review fixes, request a fresh review of the final head and wait for its result. Address new findings before proceeding.
5. Require all relevant CI and security checks to pass for the final head, including PostgreSQL concurrency checks when locking or transactional behavior changes.
6. Refresh the pull-request head and unresolved threads immediately before merging. Merge with the expected head SHA so concurrent updates cannot be silently included.

Delayed feedback on an already merged pull request must be audited against current main and addressed through a follow-up pull request. Preserve links to original findings and evidence. Historical issue #281 remains open until every inventory finding has a supported disposition; counting resolved threads is insufficient.

## Required repository setting

After the workflow is on the default branch, configure `review-evidence` as a required status check in the ruleset or branch protection for `main`, and prohibit bypass for ordinary merges. The workflow publishes this check directly against the pull-request head SHA; it does not treat the workflow run's base-branch SHA as reviewed. Only the configured reviewer can attest to final-head review, and resolved threads must have a fixing commit and validation evidence from their resolver.

The connected GitHub integration cannot read or change branch protection (GitHub returns `Resource not accessible by integration`). A repository administrator must enable the required check. Until that setting is enabled, the workflow reports failures but does not make GitHub reject a merge. This limitation remains part of the review-gate finding; Markdown checkboxes alone do not enforce it.

Resolve threads before requesting the final review. If a thread is resolved after the last review/comment event, rerun `Review evidence gate` with its pull-request number. The workflow reads trusted default-branch validator source, never PR-controlled source with its write-capable check token.

Repository administration must also enable **Require conversation resolution before merging** on `main`. This native GitHub merge requirement rechecks unresolved threads at merge time, including a thread reopened after a successful status check without a new comment. Actions has no `pull_request_review_thread` trigger; the status check alone cannot enforce this condition. Keep enforcement findings open until both the required `review-evidence` check and native conversation-resolution setting are confirmed. This integration cannot configure these administration settings.
