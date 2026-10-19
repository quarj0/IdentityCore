# Workflow template instantiation

`POST /api/v1/projects/{project_id}/workflows:instantiate` requires a tenant-scoped `Idempotency-Key`. The service records a SHA-256 digest of the source template ID, requested version, project ID and trimmed requested name at creation. Later workflow edits do not change this digest. An omitted or blank name stays blank in the digest; resolving the source template's default name happens only when creating a workflow.

Matching retries return the existing workflow, including its current name, after source archival or workflow renaming. Reusing a key for a different request returns 409. A new key that conflicts with an existing project/workflow name returns 400. New instantiations still require a published source and an approved organization for production projects.

Existing workflows created before the request digest was introduced retain an empty digest. Their original request cannot be reconstructed reliably from editable workflow state. Replays of these legacy keys return 409 with an explanation; retrieve the existing workflow by its ID. Do not automatically submit a new key after this response, since that could create a duplicate workflow.

The schema migration adds the private request digest without exposing it in workflow responses. The adoption migration reconciles existing `cloned_by_organizations` values from distinct organizations with retained workflows sourced from each template. New instantiations increment usage per workflow and adoption only for the organization's first workflow from that source. The model currently permits one tenant per organization.

Tenant catalog responses contain the published template contract. Administrator identity, ownership, risk classification and usage/adoption counters are excluded. Platform administration retains its separate template representation.

## Platform workflow authoring

Platform administrators create project-scoped drafts with an explicit ordered list
of supported step names: `consent`, `document`, `selfie`, `liveness`, `face_match`,
`decision`, `manual_review`, `webhook`. Consent and decision are required; empty,
duplicate, unknown and object-shaped steps are rejected before saving a draft.
The platform dialog defaults to consent, document and decision and lets the operator
add, remove or reorder checks. The tenant and project must match.

Edit draft sends the full step sequence along with name and description. Unsupported
legacy step data blocks this editor instead of silently dropping data; repair it
through the workflow API. Existing empty drafts can add consent and decision using
the editor. Archived workflows cannot be edited. Edits to a published workflow reset
its status to draft; retained workflow versions and policies keep their original
contents. Publishing creates a new immutable version and policy, subject to current
organization approval and policy validation. These workflows are tenant/project
records; global template publication is a separate lifecycle.

## Existing workflows and legacy lineage

First-workflow onboarding reloads the selected sandbox project's existing workflows
before showing a new creation form. It restores the configuration link even when no
published templates remain. REST clones preserve template lineage but clear both the
instantiation key and request digest, so the clone cannot collide with or impersonate
the source request. Collection/detail responses exclude deleted workflows and eagerly
load source-template lineage.

Apply `workflows.0006` and `verifications.0025` in a planned maintenance window,
with workflow publication and evidence generation paused. These are data repairs,
not automatic rolling-schema expansion; keep rollout guards intact. Fresh installs
also use defensive historical backfills. Snapshot construction and migration 0017
preserve legacy JSON settings as stored, including scalar/list values; this does not
authorize publishing new workflows with invalid settings.

The original name backfill used the mutable parent workflow name. Recovery uses the
associated immutable published policy and its historical REST/platform naming format.
Unrecoverable or truncated names become an empty string (unavailable), never a guessed
current name. The forward repair applies only to versions published before migration
0004 was applied; newer published names remain authoritative. Case snapshots copied
from affected versions retain `workflow_name_backfill_correction`, including the old
assertion, correction source and reason. Rerunning repairs is idempotent.

Historical audit events and already-written evidence artifacts remain unchanged.
Their old assertions are historical records; use the corrected case snapshot when
issuing a new evidence report, and retain the previous artifact and correction record
under normal retention/legal-hold rules. Do not present an old artifact as proof that
a legacy mutable-name assertion was accurate.
