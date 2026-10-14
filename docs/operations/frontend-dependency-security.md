# Frontend dependency security

The workspace overrides `brace-expansion` 1.x to 1.1.21 and 5.x to 5.0.12, the patched releases for [GHSA-q2hr-2g5m-vwhr](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr). DOMPurify is overridden to 3.4.16 for the two additional DOM XSS advisories found by the workspace audit. The lockfile retains unrelated dependency versions.

As of 2026-10-13, neither `braces` nor `sprintf-js` has a patched upstream release for the following advisories. Checked-in pnpm patches provide temporary mitigations:

- [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm): `braces` limits parsed AST nesting to 64 stack entries. Excessively nested brace or parenthesis input becomes a literal pattern; compilation escapes its regex metacharacters. Expansion and stringification preserve the original literal. This bounds recursion for string input and ASTs produced by the parser. Arbitrary caller-built ASTs are outside this mitigation.
- [GHSA-hp3w-g68c-fv3c](https://github.com/advisories/GHSA-hp3w-g68c-fv3c): `sprintf-js` bounds numeric precision before native number formatting. Exponential/fixed precision is limited to 0–100; significant-digit precision to 1–100. Ordinary formatting remains unchanged, while out-of-range precision is clamped.

The patch files, their lockfile hashes, and `patchedDependencies` are version-controlled. Frozen pnpm installation applies them locally, in CI, and in the verification portal image. `pnpm test:security` exercises the package copies actually resolved by Next ESLint and Swagger UI. The developer portal lint command also runs these regressions, so the existing required frontend CI checks execute them.

Version-based scanners and Dependabot can still report `braces` 3.0.3 and `sprintf-js` 1.0.3. Do not dismiss these alerts as fixed by a released version or claim that local mitigations close them. Replace each patch with a verified upstream release when one becomes available, rerun the regressions, and confirm the resulting lockfile clears the advisory. Preserve pnpm patch installation in every build that consumes this workspace.
