# ADR 056: Immutable project environment

Status: Accepted

API-client authorization derives its environment from the bound project. Allowing
a project to change from sandbox to production before its first verification could
therefore promote an already issued sandbox secret. Project environments are now
fixed at creation, including projects with no credentials or verification activity.
REST updates reject a different environment with HTTP 400; resubmitting the current
value is valid. Names, slugs and allowed origins remain editable.

Create a separate project and issue separate credentials for another environment.
This avoids an issuance-versus-environment-edit race without depending on whether
credentials or verification rows happen to exist at validation time. Existing rows,
credentials, verification snapshots and audit artifacts are not migrated. Trusted
administrative database writes remain outside the public API contract and must
preserve this invariant.

The dashboard explains this restriction and the OpenAPI create/update descriptions
state it. Regressions cover empty projects, issued credentials, existing verification
activity, ordinary partial updates and standard errors for unsupported actions.
Protected review and merge are required before rollout.
