# Claims Engine

## Status

Architectural direction with implemented foundations. IdentityCore currently stores
extracted fields, normalized provider results, evidence snapshots, and policy-driven
decisions, but does not yet expose a complete reusable cross-workload Claims Engine.

## Purpose

A claim is a normalized statement about a subject, organization, credential, or
relationship that remains linked to supporting evidence and policy.

Examples:

- legal name is `Ama Mensah`;
- date of birth is `1998-04-12`;
- document expiry is `2031-08-01`;
- subject is over a configured age threshold;
- document identifier matched an authorized registry;
- organization is a member of an approved registry;
- a required verification policy was satisfied at a specific time.

The Claims Engine turns evidence into governed, explainable statements that future
workloads can reuse without treating provider output as unquestionable truth.

## Evidence, claims, and decisions

```text
Provider or submitted evidence
              |
              v
      Normalization and correlation
              |
              v
             Claims
              |
      +-------+-------+
      |               |
      v               v
 Policy evaluation   Application disclosure
      |
      v
   Decision
```

- **Evidence** records what was observed or produced.
- **Claims** express normalized statements supported by evidence.
- **Policies** determine whether claims and evidence satisfy a workload requirement.
- **Decisions** record the outcome and inputs used.

A claim can exist without producing a final decision, and a decision may depend on raw
evidence in addition to claims.

## Claim classes

### Extracted claim

A candidate statement extracted from submitted evidence, such as OCR text from a
document.

Extracted claims are not verified merely because extraction succeeded.

### Provider-asserted claim

A statement returned by a provider, such as a registry response or credential issuer.
Its trust depends on the provider, authorization, contract, signature, freshness, and
policy context.

### Normalized claim

A provider- or evidence-specific value mapped into a stable IdentityCore schema.

Examples include standardized date formats, country codes, document types, names, and
identifiers.

### Corroborated claim

A claim supported by multiple compatible evidence sources according to a versioned
correlation rule.

For example, a name may be corroborated by document OCR and an authorized registry
lookup. Corroboration does not eliminate uncertainty; it records why confidence changed.

### Derived claim

A statement calculated from other claims and policy context.

Examples:

- age-over-18 derived from date of birth and evaluation date;
- document-current derived from expiry date and jurisdiction rules;
- identity-policy-satisfied derived from required evidence and thresholds.

Derived claims must record the rule and input claim versions.

### Reviewed claim

A claim accepted, corrected, rejected, or qualified by an authorized reviewer. Human
review actions remain evidence and must not silently overwrite the original extracted or
provider-asserted claim.

## Claim record

A generalized claim record should contain fields equivalent to:

```text
id
schema_id
schema_version
subject_or_entity_id
claim_type
value
value_format
status
confidence
source_evidence_ids
source_claim_ids
derivation_rule_id
derivation_rule_version
provider_id
workflow_id/workflow_version
policy_id/policy_version
valid_from
valid_until
observed_at
issued_at
revoked_at
supersedes/superseded_by
tenant_id
project_id
environment_id
purpose
retention_class
selective_disclosure_policy
```

Sensitive values should be encrypted, tokenized, hashed, or reference-based according to
use case. Not every claim should be broadly reusable or externally disclosed.

## Claim status

Possible status values include:

```text
candidate
normalized
corroborated
policy_satisfied
disputed
inconclusive
expired
revoked
superseded
deleted
```

Status describes the lifecycle and interpretation of the claim, not the technical status
of the provider invocation that produced its evidence.

## Claim provenance

Every claim must be explainable through provenance:

- evidence IDs;
- provider and capability;
- contract and schema versions;
- model or registry version where relevant;
- normalization or derivation rule;
- workflow and policy context;
- reviewer actions;
- time and freshness;
- supersession or revocation history.

A claim without provenance is untrusted application data, not a governed IdentityCore
claim.

## Normalization

Normalization creates a stable representation without pretending that uncertain evidence
is certain.

Examples:

- dates use an agreed machine-readable format;
- countries use standard codes;
- document types use platform taxonomy;
- names preserve original text and normalized forms;
- identifiers retain issuer/type context;
- confidence and source remain attached.

Normalization must not erase meaningful distinctions between legal name, preferred name,
transliterated name, OCR candidate, or reviewer-corrected name.

## Correlation and conflict resolution

Multiple sources may disagree. The Claims Engine should not resolve conflict using an
undocumented "highest confidence wins" rule.

Conflict handling may consider:

- source authority and provider assurance;
- evidence freshness;
- exact versus fuzzy match;
- document or credential validity;
- jurisdiction and workload policy;
- confidence calibration;
- reviewer intervention;
- known aliases or transliteration;
- whether the sources refer to the same subject.

Possible outcomes include a selected claim with reasons, a set of alternatives, a
disputed claim, a request for more evidence, or Manual Review.

## Freshness, validity, and revocation

Claims are time-bound.

A claim may have:

- observation time;
- effective time;
- expiry time;
- provider freshness limit;
- policy freshness requirement;
- credential or registry revocation state;
- supersession history.

An identity verification completed months ago may not satisfy a workload requiring a
fresh registry check. Applications should request policy satisfaction rather than assume
that any historical claim remains current.

## Selective disclosure

Future workloads should disclose only the minimum claim required.

Examples:

- disclose `age_over_18 = true` rather than date of birth;
- disclose that a document was current at evaluation time rather than its number;
- disclose policy satisfaction and assurance context rather than raw biometric scores;
- disclose a registry membership result without unrelated registry attributes.

Selective disclosure must remain purpose-, tenant-, environment-, and authorization-
scoped and auditable.

## Reusable claims

Reusable claims can reduce repeated collection, but introduce important risks:

- stale evidence;
- context mismatch;
- consent and purpose changes;
- broader breach impact;
- incorrect cross-workload assumptions;
- revocation and deletion propagation;
- hidden elevation of assurance.

A reusable claim therefore requires explicit policy for freshness, assurance, permitted
purposes, disclosure, revocation, and supporting evidence availability.

IdentityCore should not market all verification outputs as reusable identity credentials
until these controls are implemented.

## Claims and providers

Providers emit evidence and may assert claims, but the platform owns normalization,
provenance, lifecycle, and policy interpretation.

A provider-specific field must not become a global claim type without a documented
schema and mapping. Replacing a provider should not force application clients to change
the meaning of a stable IdentityCore claim.

## Claims and Manual Review

Reviewers may:

- confirm a candidate claim;
- correct a normalization error;
- mark a conflict unresolved;
- reject unsupported evidence;
- request additional evidence;
- approve a claim under maker-checker policy.

The review action creates new evidence and claim state. Original provider evidence remains
preserved according to retention policy.

## Privacy and deletion

Claims may contain highly sensitive personal information. Controls include:

- purpose limitation;
- field-level protection;
- tenant and environment isolation;
- minimal API disclosure;
- access auditing;
- retention classes;
- legal holds;
- subject export and redaction;
- deletion, anonymization, revocation, and descendant propagation.

Derived claims must be deleted or invalidated when required supporting evidence or source
claims are deleted, unless a documented legal basis permits retention of a minimal audit
fact.

## API direction

A future public claims API may support:

- requesting claims through a workflow;
- retrieving allowed normalized claims;
- inspecting provenance summaries;
- checking freshness and status;
- requesting policy satisfaction;
- revoking or superseding organization-created claims;
- selective disclosure tokens or attestations.

The API must not expose raw provider payloads or unrestricted evidence graphs by default.
Concrete endpoint documentation should only be published after contracts are implemented
and represented in OpenAPI and SDKs.

## Current foundations

IdentityCore already contains useful building blocks:

- OCR and structured extracted fields;
- normalized document and biometric provider results;
- verification subjects and document records;
- versioned workflows and policy snapshots;
- versioned decision input snapshots;
- provider and model provenance;
- reviewer decisions and maker-checker controls;
- subject export, deletion, and retention workflows.

The next architectural step is to consolidate common claim schemas, provenance, conflict,
freshness, revocation, and disclosure rules without destabilizing the working
verification workload.

## Related documentation

- [Canonical Architecture](../../ARCHITECTURE.md)
- [Evidence Model](evidence-model.md)
- [Capability Model](capability-model.md)
- [Provider Runtime](provider-runtime.md)
