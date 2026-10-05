# Pull-request review gate

Before merging a pull request:

1. Review the complete change and request the configured GitHub review. Wait for the review to finish; an empty thread list while a review is running is not completion.
2. Reproduce each substantive finding against the current code. Fix valid findings with an appropriate regression or explain why the finding is superseded or inapplicable, linking current code and validation.
3. Reply to each original review thread with the fixing commit and evidence. Resolve a thread only after that evidence exists. Never infer correctness from GitHub's resolved flag.
4. After review fixes, request a fresh review of the final head and wait for its result. Address new findings before proceeding.
5. Require all relevant CI and security checks to pass for the final head, including PostgreSQL concurrency checks when locking or transactional behavior changes.
6. Refresh the pull-request head and unresolved threads immediately before merging. Merge with the expected head SHA so concurrent updates cannot be silently included.

Delayed feedback on an already merged pull request must be audited against current main and addressed through a follow-up pull request. Preserve links to original findings and evidence. Historical issue #281 remains open until every inventory finding has a supported disposition; counting resolved threads is insufficient.
