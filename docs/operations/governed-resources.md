# Governed evidence and reusable claims

This runbook describes the public v0.4 contract in
[OpenAPI](../openapi/identitycore-public-api.yaml). Evidence and claims are
independent tenant/project/subject resources. Existing verification captures,
provider checks and decision snapshots keep their existing contracts. Creating a
resource does not automatically publish it, authorize reuse or make it verified.

## Access and authority

Use the existing user JWT authentication or a project-bound API credential.
Every resource request selects an exact project, and value access selects a
purpose. Foreign and unknown identifiers are indistinguishable. The service
rechecks current actor, tenant, project, environment, grants and source state on
reads, writes and idempotent retries. Responses use `Cache-Control: no-store`.

| Operation | User permission | API credential scope |
| --- | --- | --- |
| Read evidence/schema/lineage | `read_evidence` | `evidence:read` |
| Create/revoke evidence | `manage_evidence` | `evidence:write` |
| Read claims/policies/lineage | `read_claims` | `claims:read` |
| Create/revoke claims, propose policy | `manage_claims` | `claims:write` |
| Issue/revoke disclosure | `disclose_claims` | `claims:disclose` |
| Schema administration | `manage_evidence` | User only |
| Purpose authorizations and holds | `manage_subject_privacy` | User only |
| Claim conflict review | `review_verification` and `manage_claims` | User only |
| Reuse policy approval | `manage_subject_privacy` and `read_claims` | User only |

Additional source reads require the corresponding read permission. Grant,
policy and conflict approvals require a different actor from their proposer or
selected assertion's creator, as applicable. Built-in administrator roles gain
the new narrow permissions through migration and onboarding; existing custom
roles are not expanded. API scopes do not override human-only governance.

## Create evidence

1. An authorized user registers an immutable schema using `POST /evidence/schemas`.
   Set `kind` to `evidence` or `claim`, provide a versioned name and a bounded
   Draft 2020-12 object schema. Disclosure fields must be declared explicitly.
   The supported subset excludes external references, regular expressions and
   combinatorial evaluation; it is not arbitrary JSON Schema execution.
2. Create `POST /evidence/authorizations` for the subject, project, purpose,
   allowed operations and validity. Consent grants reference the actual current
   consent record. Other supported legal-basis declarations require independent
   privacy approval and retained justification. A declaration is not a legal opinion.
   Cross-purpose processing requires explicit `reuse_from_ids` and revalidation
   of every source grant. Holds never grant continued processing authority.
3. `POST /evidence/` supplies the schema, authorization, subject, exact project,
   observation/validity/deletion deadlines, payload and provenance. Provider
   evidence may bind `source_check_id` to an existing completed check. Source
   IDs form bounded earlier-resource lineage; caller assertions do not become
   independent authoritative or provider evidence merely by choosing a label.
4. List or retrieve with the exact project and purpose. `include_payload=true`
   explicitly requests audited decryption. Lineage endpoints return metadata and
   source edges, without payloads. Payload and provenance are encrypted and hashed.
5. Correct by creating a new record with `supersedes_id`. Revocation and
   supersession invalidate dependent use. Values are never edited in place.

Mutation requests require the existing `Idempotency-Key` contract. Unknown body
fields are rejected. See OpenAPI for exact required fields, limits and envelopes;
all four API SDKs expose named methods under `.governed` (`.Governed` in .NET).

## Create, resolve and reuse claims

`POST /claims/` accepts evidence/claim sources under a claim schema. Raw assertions
remain candidates. Version 1 rules are `copy`, `field`, `normalize_name`, `iso_date`,
`age_over`, `document_current` and `exact_corroboration`. Rules are deterministic,
versioned and retain their input graph. Independent corroboration requires
independent provider-bound completed roots. Dates use UTC; date-sensitive
predicates expire by the next UTC day. Expiry is bounded by source validity.

Conflicting current claims remain explicit. `POST /claims/{id}/review` records
an independently authorized choice, dispute or request for more evidence, bound
to the complete current member set. A later conflicting member invalidates an
earlier choice. Confidence alone never resolves a conflict. Source revocation,
erasure, expiry or supersession propagates to descendants.

Propose a versioned reuse policy with allowed purposes, schema fields, claim
classes, minimum confidence and maximum age. A separate privacy reviewer must
approve it before use. Freshness uses the oldest supporting source, not the time
of copying. `POST /claims/{id}/evaluate` returns eligibility and bounded reason
codes; it does not disclose values or override authorization.

Issue a disclosure using `POST /claims/disclosures`: select permitted claims and
fields, approved policies, an exact project/purpose grant and the audience API
client. Its maximum lifetime is 900 seconds. The raw token appears only on the
first successful issuance response; a repeated idempotent request returns the
receipt with no raw token. The database stores only its hash. If the response is
lost, revoke that receipt and issue a new disclosure with a new idempotency key.

The audience redeems with its own active `claims:read` credential, matching
project, request idempotency key and `X-Disclosure-Token`. Each redemption,
including a retry, revalidates live grants, sources, policies, conflicts and
expiry. Only selected fields or permitted derived predicates are returned.
Redeemed values and raw tokens are not persisted in idempotency responses.
This is access-controlled field selection, not a zero-knowledge credential format.

## Retention, holds and deletion

Evidence, claims, purpose grants, disclosure receipts and conflict resolutions
have explicit deletion deadlines. The beat schedule runs bounded retirement every
five minutes, fairly rotating tenants. Operators may run:

```sh
python backend/django/manage.py retire_governed_resources --tenant TENANT_PUBLIC_ID --limit 100
```

Use the existing retention worker and beat deployments. Verify scheduling, queue
consumption, failures and key availability before production use. Key outages fail
closed; do not substitute plaintext or treat unavailable content as authorized.

Subject/project holds preserve encrypted content while preventing unauthorized
use. A subject deletion request immediately records a processing restriction and
revokes grant/reuse/disclosure use even if a hold defers destruction. Actual erasure
scrubs encrypted values, free-form provenance and reasons, retaining the permitted
pseudonymous audit and lineage metadata. Subject exports include governed resource
metadata and explicit value redactions under the existing export boundary; they
are not an unrestricted raw evidence/biometric export.

Release a hold only under the existing accountable privacy process. Releasing a
hold does not restore revoked grants or claims. Backups, external processors and
independent legal/security assurance remain part of deployment operations.
