# Review evidence gate deployment

The validator publishes `review-evidence` through a dedicated GitHub App. The workflow's ordinary `GITHUB_TOKEN` is read-only. Review events use a credential-free signal workflow; `workflow_run` performs validation from the default branch. PR source and artifacts never execute with the publisher token.

## Required administration

Before this gate can enforce merging, a repository administrator must complete these settings:

1. Register and install a dedicated GitHub App for this repository with Contents, Pull requests and Actions read permissions, and Checks write permission. Do not grant it administration, source write, or merge permissions.
2. Create the `review-evidence-publisher` environment. Configure its deployment branch policy to allow only the literal default branch (`main`), excluding pull-request refs and every feature branch. Store `REVIEW_GATE_APP_CLIENT_ID` as an environment variable and `REVIEW_GATE_APP_PRIVATE_KEY` as an environment secret. The private key must exist only in this environment, never as a repository or organization secret accessible to PR jobs.
3. Require `review-evidence` on `main` with the dedicated App selected as its expected source. A same-named check from GitHub Actions must not satisfy it.
4. Require conversation resolution at merge time. Thread unresolution must block merging even before the queued validator runs.
5. Restrict updates of `main` to administrator PR merges through the `Trusted main mergers` ruleset. Its only bypass actor is repository administrator (role 5), with `pull_request` bypass mode. Existing branch protection continues to apply to administrators. Contributors cannot merge using a cached check while asynchronous revalidation is queued. Trusted administrators must use the live merge command below.
6. Require `CI required` and `Security required` with GitHub Actions (App ID 15368) as their expected publisher. Their always-running summary jobs require every corresponding workflow job to succeed. Preserve existing CI, Security and review requirements when changing protection. Install the gate through a controlled bootstrap: its validator and signal must be on the default branch before its dedicated check can run. Keep the protection and publisher reviews open until bootstrap and the enforcement checks below have evidence.

Use a standalone disposition with the commit SHA and canonical validation result; put implementation discussion in a separate preceding reply. Validation evidence must use an affirmative clause such as `Validation: all 75 gate regression tests passed.` or `regression tests pass.`. Use exactly one canonical fixing-commit reference. If several resolver dispositions share the latest timestamp, every tied disposition must contain valid fixing and validation evidence. Creation order cannot establish edit order. After a retraction, post restoring evidence in a later timestamp second. Every clause must be a canonical fixing-commit reference, the `Validation` label, or a canonical affirmative result. Additional prose belongs in a preceding reply. This rejects skipped, omitted, disabled, incomplete or arbitrary follow-up claims without relying on a negative-word vocabulary. Negative quantifiers, zero results, contracted negatives and speculative result wording do not count as passing evidence.

Disposition evidence must be authored by a fixed trusted maintainer: the repository owner by default, or `REVIEW_GATE_RESOLVER_LOGIN` configured in the protected publisher environment. The actor who clicks Resolve is not an evidence authority. Unresolving a thread blocks merging through native conversation protection; re-resolving it cannot manufacture or replace the required trusted evidence. New feedback and edited or deleted evidence still require revalidation and a later final-head review.

Check runs are attached to repository commits, so multiple open PRs sharing the same head SHA are blocked. The publisher and live merger inspect open PR heads in both evidence snapshots; bucket preparation supplies the first snapshot to keep REST calls bounded. Give each open PR a unique head commit and rerun the publisher after removing a collision.

Discovery selects PR numbers only. Each bucket concurrently publishes pending checks for every selected discovered head before refreshing individual PRs or collecting evidence, inside a stable concurrency group determined by the PR number modulo 8. Immediately before each serial assessment, refresh the prepared PR; a moved current head receives a new pending check and its superseded pending check is completed as failure. Every event for a PR uses the same group. Each group refreshes and validates all of its open PRs, so queued-job replacement cannot drop another PR, and the matrix never exceeds eight jobs. Active assessments are not canceled by newer discovery, and queued jobs create no App checks. This prevents canceled or out-of-order discovery from orphaning the latest required check.

CI, Security and the publisher respond to PR base edits. Accepted PR workflow runs must identify the current PR number, head and target branch. When GitHub omits fork association metadata, a separate job with no checkout, PR execution or permissions records the immutable PR event in its job log. The collector reads only that job’s fixed step from the run-attempt log archive and binds its unique record to the run ID, attempt, PR number, head and base. Artifacts and logs from other jobs cannot supply this proof. Missing proof or evidence from a previous target fails closed. Active unassociated runs remain blocking. Immutable proof downloads are cached across snapshots. For partial reruns that omit a previously successful proof job, the collector searches earlier attempts of the same run and validates the proof against its actual originating attempt. Only an absent proof permits this fallback; malformed, duplicated or conflicting proof remains blocking. The current run must still have a successful latest attempt. An obsolete run with unusable proof remains unaffiliated and cannot satisfy validation or veto newer verified evidence. A current unaffiliated run remains blocking; authorization, rate-limit and service errors fail collection. A base change during collection blocks validation and the live merger.

Publisher evidence queries each trusted CI and Security identity for PR runs in both snapshots; the live merger additionally checks push runs. Each event query is paginated. At GitHub’s 1000-run filtered-history ceiling, fail closed: sequential active-status searches cannot establish complete history because a run can transition between their filters. No capped history can satisfy merge evidence. Workflow-run discovery handles completion only. Empty CI/Security association metadata narrows discovery by the immutable run head and, when available, source repository and branch; only affected buckets are scheduled. A normal fork update therefore triggers two bounded bucket refreshes rather than six repository-wide sweeps. Native required CI and the live merger block active runs before completion. Declared commit evidence uses targeted ancestry comparisons against the full current head, avoiding both the PR commit endpoint cap and a repeated scan of the entire repository history. Ambiguous abbreviations and non-ancestor commits are rejected. Fixing references must also be outside the current PR base history; a second immutable comparison rejects commits already reachable from that base. Review-head identity remains a separate proof. SHA discovery accepts either letter case and normalizes comparison tokens. Tied latest resolver timestamps require every tied disposition to provide valid fixing and validation evidence; creation order cannot establish edit order. Protected file definitions are compared in one GraphQL query. Eight stable buckets and cached immutable workflow metadata keep a 257-PR bulk validation, including fork proofs, below the 5,000-request installation REST budget in the regression fixture. Unrelated issue comments and formal reviews are excluded from evidence snapshots and ordinary issue-comment events do not trigger publishing.

The App token is scoped to this repository, explicitly requests the needed permissions, and is revoked after each job. Both discovery and per-PR assessment use the protected environment and the dedicated token. Missing configuration fails the action; there is no GitHub Actions publisher fallback.

## Enforcement checks

- Dispatch `Review evidence gate` from `main` for a disposable PR and confirm the check's publisher is the dedicated App.
- Confirm a PR job requesting the publisher environment cannot obtain its key because its ref is not `main`.
- Confirm a same-named GitHub Actions check cannot satisfy the required dedicated-App check.
- Unresolve a substantive thread and confirm merging is blocked by conversation resolution. Submit/edit/dismiss a review and edit/delete a review comment; confirm the signal triggers default-branch validation and invalidates prior evidence.
- Confirm a new head, changed protected definition, missing trusted-maintainer evidence, or failing CI/Security prevents success. Re-resolve a thread under another actor and confirm this does not substitute that actor for the configured evidence author.
- Record configuration and validation evidence before resolving the administration reviews on #364.

On 2026-10-08, authenticated `gh` administration verified strict main protection requiring `review-evidence` from dedicated App `5218906`, plus `CI required` and `Security required` from Actions `15368`. Conversation resolution and protection apply to administrators; ruleset `24627093` permits administrator main updates only through PR merges. The App credentials are configured exclusively in the literal-main publisher environment, with repository installation limited to the intended read permissions and Checks write. After reviewed bootstraps #383 and #386, temporary probe #384 verified environment denial on its feature branch and rejection of a successful same-name Actions check alongside failing dedicated App evidence. The owned probe was closed and its branch removed. Deployment reviews on #364 are resolved with that evidence; its atomic evidence-timing review is disposed by the owner’s explicit 2026-10-13 acceptance of the documented trusted-administrator limitation. Reverify the live configuration before merging.

Implementation reference: [actions/create-github-app-token](https://github.com/actions/create-github-app-token).

## October 14 restoration and verification

On 2026-10-14, authenticated administration found that the native branch-protection
endpoint for `main` returned HTTP 404 ("Branch not protected"). The separate
`Trusted main mergers` ruleset `24627093` was still active. The October 8 receipt
above is a historical snapshot and does not establish uninterrupted enforcement.

Administration restored native protection and read it back: strict up-to-date
checks require `CI required` and `Security required` from Actions App `15368`,
and `review-evidence` from dedicated App `5218906`; administrator enforcement
and conversation resolution are enabled, with force pushes and deletions disabled.
The existing main update ruleset remains active with administrator-role
pull-request-only bypass. The publisher environment was already restricted to the
literal `main` branch; its custom branch policy was reverified without changing it.
The trusted merger must verify these live controls again before every merge.

## Trusted live merge command

Load the command and validator from the fetched default branch, not a PR checkout:

```sh
git fetch origin main
git worktree add --detach /tmp/identitycore-trusted-merge origin/main
node /tmp/identitycore-trusted-merge/.github/scripts/merge-reviewed-pr.cjs --repo quarj0/IdentityCore --pr 123 --merge
```

Without `--merge`, the command checks readiness. It requires administrator identity, native administrator and conversation protection, the dedicated-App required check, and the administrator-only update ruleset. It then independently reads and evaluates current review evidence, protected definitions, declared commit ancestry, and the latest final-head PR and any push CI/Security runs; active runs block, while superseded failures and unrelated dispatches do not. A previously successful check cannot skip this assessment. It checks the head again and submits a squash merge through the native pull-request API with the expected head SHA. GitHub enforces repository protections on that request. The command does not request an administrator override. This avoids the `gh pr merge` preflight interpreting a generic BLOCKED status as a refusal even when the administrator has PR-only ruleset authority. This is the authorized merger path; contributors and PR jobs cannot invoke an administrative merge. Administrators remain trusted because they can change repository protection itself.

The live merger also requires strict native status-check protection so GitHub rejects a stale base at merge time; an expected-head lease alone does not protect the base. It rechecks PR and push CI after final live evidence collection.

During an actual merge, the command temporarily installs a native branch update ruleset covering every branch except `main`, with zero bypass actors. It checks that guard before merging and removes its own ruleset in a `finally` block. GitHub therefore blocks a merge retargeted to any other branch at the update operation. Non-main updates briefly pause during this window. Read-only validation creates no guard. The CLI records the unique name, ruleset ID and lifecycle in `.identitycore-merge-guard-PR.json`; after a process crash, inspect that record and delete only its exact repository ruleset. Cleanup errors report the ID and require recovery before another merge.

The initial bootstrap is a reviewed administrator merge before the App-bound check is enabled. Require all final-head CI and a fresh configured review, inspect every thread, and keep #364's deployment reviews open until actual publisher and protection validation is complete.

## Governed changes to protected definitions

A protected-definition change requires independent review of the exact proposed head and explicit administrator approval in the protected publisher environment. Set `REVIEW_GATE_APPROVED_UPDATES` to a JSON object with the full current `main` SHA in `base`, an `expires_at` timestamp within the next 24 hours, and a `heads` map from full reviewed head SHA to the exact protected paths approved for change. Only the listed validator, workflows, merger and policy paths are accepted. The approved main base must be an ancestor of the head, ensuring GitHub cannot combine unreviewed main edits with the approved protected blobs. A different head, moved main branch, expired approval or unlisted path retains the normal definition mismatch failure.

Publish that value with the environment-variable API using a local JSON request file containing `name` and `value`; keep approval out of repository-wide variables and PR-controlled files. The publisher receives it only through its main-only environment. The live merger reads it and the configured resolver login from that environment through authenticated `gh`, independently of local environment variables. Remove the approval after merge with `gh api --method DELETE repos/OWNER/REPO/environments/review-evidence-publisher/variables/REVIEW_GATE_APPROVED_UPDATES`. Review completion, trusted dispositions, conversation resolution, CI and the App check remain mandatory; this approval permits only the reviewed definition differences. The validator verifies main's base and approval expiry again after assessment. After the final live assessment, CI fetch and guard check, the merger rereads approval and resolver policy and verifies approval equality, expiry, current main base and ancestry before the final head lease.

## Merge API limitation

The command collects mutable review evidence again after its other preflight reads, then checks the PR head and immediately requests the merge. GitHub's merge API supports an expected commit SHA but no expected review-evidence version or transaction that locks comment edits and review dismissal. An evidence edit can therefore race between the final collection and merge even when the SHA is unchanged. Native conversation protection and CI remain enforced, but an atomic guarantee for mutable review content cannot be claimed. Keep any review requiring that guarantee open until the repository owner accepts this documented trusted-administrator limitation or chooses a different evidence policy.

Bucket initialization publishes pending checks from the discovered PR heads before any fallible per-PR refresh. Transient check creation is retried. Each prepared entry then refreshes the live PR, invalidates a moved head, and completes a previously created pending check as failure if refresh fails. An unavailable GitHub check API cannot provide an atomic invalidation guarantee; trusted mergers must still perform the live assessment and fail closed on collection errors.

On 2026-10-13, repository owner `quarj0` explicitly accepted the documented non-atomic review-evidence timing limitation for trusted administrator merges. This is a policy acceptance, not an atomicity fix. All native protection, current-head independent review, trusted dispositions, live evidence reassessment and temporary target-guard requirements remain mandatory. The accepted policy does not permit skipping inaccessible administrative checks or merging with failing CI/Security.
