# Review evidence gate deployment

The validator publishes `review-evidence` through a dedicated GitHub App. The workflow's ordinary `GITHUB_TOKEN` is read-only. Review events use a credential-free signal workflow; `workflow_run` performs validation from the default branch. PR source and artifacts never execute with the publisher token.

## Required administration

Before this gate can enforce merging, a repository administrator must complete these settings:

1. Register and install a dedicated GitHub App for this repository with Contents, Pull requests and Actions read permissions, and Checks write permission. Do not grant it administration, source write, or merge permissions.
2. Create the `review-evidence-publisher` environment. Configure its deployment branch policy to allow only the literal default branch (`main`), excluding pull-request refs and every feature branch. Store `REVIEW_GATE_APP_CLIENT_ID` as an environment variable and `REVIEW_GATE_APP_PRIVATE_KEY` as an environment secret. The private key must exist only in this environment, never as a repository or organization secret accessible to PR jobs.
3. Require `review-evidence` on `main` with the dedicated App selected as its expected source. A same-named check from GitHub Actions must not satisfy it.
4. Require conversation resolution at merge time. Thread unresolution must block merging even before the queued validator runs.
5. Preserve existing CI, Security and review requirements when changing protection. Install the gate through a controlled bootstrap: its validator and signal must be on the default branch before its dedicated check can run. Keep the protection and publisher reviews open until bootstrap and the enforcement checks below have evidence.

The App token is scoped to this repository, explicitly requests the needed permissions, and is revoked after each job. Both discovery and per-PR assessment use the protected environment and the dedicated token. Missing configuration fails the action; there is no GitHub Actions publisher fallback.

## Enforcement checks

- Dispatch `Review evidence gate` from `main` for a disposable PR and confirm the check's publisher is the dedicated App.
- Confirm a PR job requesting the publisher environment cannot obtain its key because its ref is not `main`.
- Confirm a same-named GitHub Actions check cannot satisfy the required dedicated-App check.
- Unresolve a substantive thread and confirm merging is blocked by conversation resolution. Submit/edit/dismiss a review and edit/delete a review comment; confirm the signal triggers default-branch validation and invalidates prior evidence.
- Confirm a new head, changed protected definition, missing resolver evidence, or failing CI/Security prevents success.
- Record configuration and validation evidence before resolving the administration reviews on #364.

The GitHub connector used for this change returns 403 for branch-protection administration and cannot provision Apps, environment secrets or deployment policies. Local administrator credentials were also unavailable. These are deployment prerequisites, not completed settings.

Implementation reference: [actions/create-github-app-token](https://github.com/actions/create-github-app-token).
