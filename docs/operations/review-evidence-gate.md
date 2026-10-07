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

Use a standalone disposition with the commit SHA and canonical validation result; put implementation discussion in a separate preceding reply. Validation evidence must use an affirmative clause such as `Validation: all 75 gate regression tests passed.` or `regression tests pass.`. Negative quantifiers, zero results, contracted negatives and speculative result wording do not count as passing evidence.

Disposition evidence must be authored by a fixed trusted maintainer: the repository owner by default, or `REVIEW_GATE_RESOLVER_LOGIN` configured in the protected publisher environment. The actor who clicks Resolve is not an evidence authority. Unresolving a thread blocks merging through native conversation protection; re-resolving it cannot manufacture or replace the required trusted evidence. New feedback and edited or deleted evidence still require revalidation and a later final-head review.

Discovery selects PR numbers only. Each assessment reads the current head and creates its pending check inside a stable concurrency group determined by the PR number modulo 8. Every event for a PR uses the same group. Each group refreshes and validates all of its open PRs, so queued-job replacement cannot drop another PR, and the matrix never exceeds eight jobs. Active assessments are not canceled by newer discovery, and queued jobs create no App checks. This prevents canceled or out-of-order discovery from orphaning the latest required check.

CI, Security and the publisher respond to PR base edits. Accepted PR workflow runs must identify the current PR number, head and target branch; When GitHub omits fork association metadata, a separate job with no checkout, PR execution or permissions records the immutable PR event in its job log. The collector reads only that job’s fixed step from the run-attempt log archive and binds its unique record to the run ID, attempt, PR number, head and base. Artifacts and logs from other jobs cannot supply this proof. Missing proof or evidence from a previous target fails closed. Active unassociated runs remain blocking. Immutable proof downloads are cached across snapshots. A base change during collection blocks validation and the live merger.

Workflow evidence is queried separately for each trusted CI and Security identity and PR/push event and paginated in both snapshots, avoiding unrelated-run search caps. Declared commit evidence uses targeted ancestry comparisons against the full current head, avoiding both the PR commit endpoint cap and a repeated scan of the entire repository history. Ambiguous abbreviations and non-ancestor commits are rejected. Protected file definitions are compared in one GraphQL query. Eight stable buckets and cached immutable workflow metadata keep a 257-PR bulk validation, including fork proofs, below the 5,000-request installation REST budget in the regression fixture. Unrelated issue comments and formal reviews are excluded from evidence snapshots and ordinary issue-comment events do not trigger publishing.

The App token is scoped to this repository, explicitly requests the needed permissions, and is revoked after each job. Both discovery and per-PR assessment use the protected environment and the dedicated token. Missing configuration fails the action; there is no GitHub Actions publisher fallback.

## Enforcement checks

- Dispatch `Review evidence gate` from `main` for a disposable PR and confirm the check's publisher is the dedicated App.
- Confirm a PR job requesting the publisher environment cannot obtain its key because its ref is not `main`.
- Confirm a same-named GitHub Actions check cannot satisfy the required dedicated-App check.
- Unresolve a substantive thread and confirm merging is blocked by conversation resolution. Submit/edit/dismiss a review and edit/delete a review comment; confirm the signal triggers default-branch validation and invalidates prior evidence.
- Confirm a new head, changed protected definition, missing trusted-maintainer evidence, or failing CI/Security prevents success. Re-resolve a thread under another actor and confirm this does not substitute that actor for the configured evidence author.
- Record configuration and validation evidence before resolving the administration reviews on #364.

Authenticated `gh` administration verified that `main` already enforces conversation resolution and applies protection to administrators. The `review-evidence-publisher` environment is configured with a custom deployment policy allowing only the literal `main` branch. The dedicated App is registered and its environment credentials are configured. Repository installation is verified with only the intended read permissions and Checks write permission. The App-bound required check remains a deployment prerequisite. GitHub App registration uses GitHub settings or its browser manifest flow; repository administration through `gh api` does not itself register an App.

Implementation reference: [actions/create-github-app-token](https://github.com/actions/create-github-app-token).

## Trusted live merge command

Load the command and validator from the fetched default branch, not a PR checkout:

```sh
git fetch origin main
git worktree add --detach /tmp/identitycore-trusted-merge origin/main
node /tmp/identitycore-trusted-merge/.github/scripts/merge-reviewed-pr.cjs --repo quarj0/IdentityCore --pr 123 --merge
```

Without `--merge`, the command checks readiness. It requires administrator identity, native administrator and conversation protection, the dedicated-App required check, and the administrator-only update ruleset. It then independently reads and evaluates current review evidence, protected definitions, declared commit ancestry, and the latest final-head PR and any push CI/Security runs; active runs block, while superseded failures and unrelated dispatches do not. A previously successful check cannot skip this assessment. It checks the head again and merges with an expected-head lease, without `--admin` or protection bypass. This is the authorized merger path; contributors and PR jobs cannot invoke an administrative merge. Administrators remain trusted because they can change repository protection itself.

The live merger also requires strict native status-check protection so GitHub rejects a stale base at merge time; an expected-head lease alone does not protect the base. It rechecks PR and push CI after final live evidence collection.

During an actual merge, the command temporarily installs a native branch update ruleset covering every branch except `main`, with zero bypass actors. It checks that guard before merging and removes its own ruleset in a `finally` block. GitHub therefore blocks a merge retargeted to any other branch at the update operation. Non-main updates briefly pause during this window. Read-only validation creates no guard. The CLI records the unique name, ruleset ID and lifecycle in `.identitycore-merge-guard-PR.json`; after a process crash, inspect that record and delete only its exact repository ruleset. Cleanup errors report the ID and require recovery before another merge.

The initial bootstrap is a reviewed administrator merge before the App-bound check is enabled. Require all final-head CI and a fresh configured review, inspect every thread, and keep #364's deployment reviews open until actual publisher and protection validation is complete.

## Governed changes to protected definitions

A protected-definition change requires independent review of the exact proposed head and explicit administrator approval in the protected publisher environment. Set `REVIEW_GATE_APPROVED_UPDATES` to a JSON object with the full current `main` SHA in `base`, an `expires_at` timestamp within the next 24 hours, and a `heads` map from full reviewed head SHA to the exact protected paths approved for change. Only the listed validator, workflows, merger and policy paths are accepted. The approved main base must be an ancestor of the head, ensuring GitHub cannot combine unreviewed main edits with the approved protected blobs. A different head, moved main branch, expired approval or unlisted path retains the normal definition mismatch failure.

Publish that value with the environment-variable API using a local JSON request file containing `name` and `value`; keep approval out of repository-wide variables and PR-controlled files. The publisher receives it only through its main-only environment. The live merger reads it and the configured resolver login from that environment through authenticated `gh`, independently of local environment variables. Remove the approval after merge with `gh api --method DELETE repos/OWNER/REPO/environments/review-evidence-publisher/variables/REVIEW_GATE_APPROVED_UPDATES`. Review completion, trusted dispositions, conversation resolution, CI and the App check remain mandatory; this approval permits only the reviewed definition differences. The validator verifies main's base and approval expiry again after assessment. After the final live assessment, the merger rereads approval and resolver policy and verifies approval equality, expiry, current main base and ancestry before the final head lease.

## Merge API limitation

The command collects mutable review evidence again after its other preflight reads, then checks the PR head and immediately requests the merge. GitHub's merge API supports an expected commit SHA but no expected review-evidence version or transaction that locks comment edits and review dismissal. An evidence edit can therefore race between the final collection and merge even when the SHA is unchanged. Native conversation protection and CI remain enforced, but an atomic guarantee for mutable review content cannot be claimed. Keep any review requiring that guarantee open until the repository owner accepts this documented trusted-administrator limitation or chooses a different evidence policy.
