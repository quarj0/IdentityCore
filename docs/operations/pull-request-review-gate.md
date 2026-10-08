# Pull-request review gate

This is the reviewer checklist. The authoritative **deployment, native protection, publisher-identity, approved-maintenance and merge** specification is [Review evidence gate deployment](review-evidence-gate.md). Follow that specification in full; this checklist is **not** an alternative branch-protection setup procedure.

## Before merging

1. Review the complete diff and request the configured independent review for the exact final head. An empty thread list while review is running does not mean review is complete.
2. Reproduce substantive findings against the current implementation. Fix valid findings with regression tests or provide verifiable current-code evidence that a finding is inapplicable or superseded.
3. Reply to each original thread with a trustworthy fixing commit and affirmative validation evidence. Resolve only after the evidence exists; a resolved GitHub flag alone does not prove implementation.
4. After the final code and disposition changes, request a fresh configured review of that exact head. Address any newly reported findings and repeat if the head or mutable evidence changes.
5. Require completed, successful CI and Security for the **current** PR head, not a previous head or a pending workflow. Include PostgreSQL concurrency tests when transactions or locks change.
6. Have a trusted repository administrator use the **live merger** documented in [Review evidence gate deployment](review-evidence-gate.md#trusted-live-merge-command). It independently refreshes review evidence, expected head, required checks, protected definitions and administrative policies before requesting a native GitHub merge. Do not replace it with a checklist-only merge or rely on an expected-head SHA as proof that review evidence is immutable.

For delayed feedback on already-merged pull requests, assess the finding against the current `main` and use a separate remediation PR. Link original findings to tested fixes. Keep [historical audit #281](https://github.com/quarj0/IdentityCore/issues/281) open until the entire inventory has evidence-backed dispositions.

## Publisher identity and native branch protection

The implemented `.github/workflows/review-gate.yml` publishes `review-evidence` through the dedicated **IdentityCore Review Evidence** GitHub App, not GitHub Actions' shared check identity. Its ordinary `GITHUB_TOKEN` lacks Checks write permission. The review-signal workflow is credential-free, and publisher credentials are isolated to the `review-evidence-publisher` environment with a **literal `main`-only** deployment policy. There is no shared-Actions-token fallback. Seeing an App-authored check is not, by itself, proof that `main` requires that exact App as the trusted publisher.

An administrator must verify **all** native controls specified in [Required administration](review-evidence-gate.md#required-administration) and the [Enforcement checks](review-evidence-gate.md#enforcement-checks), including:

- Require `review-evidence` **from the dedicated GitHub App**, not just a matching check name from GitHub Actions.
- Require `CI required` and `Security required` with GitHub Actions (App ID `15368`) as the expected publisher, and require **strict up-to-date** status checks so an outdated PR base cannot merge.
- Require conversation resolution, appropriate review requirements and enforcement for **administrators** as well as contributors.
- Restrict `main` updates using the administrator-only **Trusted main mergers** ruleset with pull-request-only administrative bypass. Use its protected trusted merger; never disable protection or use an override to force a merge.
- Keep the publisher private key exclusively in the protected, main-only environment; keep protected definition changes governed by the explicit approval process described in [Governed changes to protected definitions](review-evidence-gate.md#governed-changes-to-protected-definitions).

On 2026-10-08, authenticated repository administration verified the dedicated publisher binding and native enforcement after bootstrap PRs [#383](https://github.com/quarj0/IdentityCore/pull/383) and [#386](https://github.com/quarj0/IdentityCore/pull/386). `main` requires `review-evidence` from App ID `5218906`, alongside strict `CI required` and `Security required` from Actions `15368`; conversation resolution and administrator enforcement are enabled, and ruleset `24627093` restricts main updates to administrator PR merges. Temporary probe [#384](https://github.com/quarj0/IdentityCore/pull/384) verified feature-branch environment denial and that a successful same-name Actions check cannot satisfy the dedicated App requirement. Its branch was removed after verification. These deployment findings are resolved with evidence on #364. The separate atomic evidence-timing review remains open pending an explicit repository-owner decision; the limitation below still applies. Reverify the live settings before each merge.

If a thread is resolved after the last review or comment event, trigger the default-branch `Review evidence gate` for that PR number. Changed review evidence, comments or review submissions must be reassessed. CI/Security workflow definitions and protected validator files are compared with trusted `main`; privileged changes require the separately approved maintenance path.

## Non-atomic evidence-to-merge limitation

GitHub can condition a native merge on the expected **head commit SHA**, but not on a version or lock of mutable review comments, resolutions, and review submissions. Evidence can change between the trusted live merger's final evidence collection and the native merge without changing that head SHA. The live merger performs repeated checks and uses native conversation protection, yet **does not provide an atomic guarantee** against every last-instant review-evidence mutation.

The administrator must follow [Merge API limitation](review-evidence-gate.md#merge-api-limitation) and make an explicit repository-owner policy decision about that residual risk; **leave the associated P1 finding open** until a supported mitigation or evidence-backed risk acceptance exists. Do not describe an expected-head lease or stale resolved thread as a full solution.
