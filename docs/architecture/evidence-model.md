# Evidence Model

## Purpose

Evidence is the durable, auditable record of what was supplied, observed, or produced
during an IdentityCore operation.

Evidence allows IdentityCore to explain:

- what happened;
- which provider or human produced a result;
- which workflow and policy were active;
- which inputs were used;
- how a claim or decision was derived;
- what must be retained, redacted, exported, or deleted.

Evidence is not automatically a verified claim or final decision.

## Design principles

1. **Provider-neutral normalization.** Core consumers depend on IdentityCore evidence schemas, not vendor payloads.
2. **Provenance is mandatory.** Evidence records where they came from and what they depended on.
3. **Interpretation is versioned.** Capability, schema, provider, model, workflow, and policy versions remain discoverable.
4. **Evidence is append-only in meaning.** Corrections create new records or supersession links rather than silently rewriting history.
5. **Raw data is minimized.** Store references or derived results where possible instead of duplicating sensitive media.
6. **Retention is explicit.** Every evidence class has retention, legal-hold, export, and deletion behavior.
7. **Integrity is verifiable.** Sensitive evidence and audit lineage include hashes, signatures, or equivalent integrity metadata where appropriate.
8. **Decisions reference snapshots.** A decision remains reproducible even after configuration changes.

## Evidence categories

### Submitted evidence

Evidence supplied by a subject, organization, operator, or application:

- document images;
- selfie or liveness media;
- entered identity attributes;
- consent acceptance;
- registry query parameters;
- organization-provided records.

Submitted evidence must retain capture source, timestamps, purpose, consent, tenant,
environment, and storage-reference metadata.

### Provider evidence

Normalized results produced by a capability provider:

- document quality issues;
- document classification candidates;
- OCR lines and extracted fields;
- face detection and similarity scores;
- liveness or PAD results;
- registry matches;
- risk signals;
- delivery or infrastructure outcomes.

Provider evidence includes capability, contract, provider, adapter, and model versions.

### System evidence

Signals produced by IdentityCore itself:

- workflow state transitions;
- policy evaluation results;
- retry and fallback reasons;
- environment and credential scope;
- capture provenance and idempotency state;
- retention and deletion outcomes.

### Human evidence

Structured findings created during Manual Review:

- reviewer reason codes;
- evidence annotations;
- quality or mismatch observations;
- escalation notes;
- maker-checker approval or rejection;
- additional-evidence requests.

Free-form notes should be minimized and protected because they may contain sensitive or
subjective information.

### External authoritative evidence

Evidence returned from authorized registries or credential issuers:

- document-validity status;
- identifier match;
- issuer signature validation;
- membership or eligibility status;
- credential revocation state.

The record must preserve source authority, legal authorization, query purpose, match
semantics, and response time.

## Evidence record

A normalized evidence record should contain fields equivalent to:

```text
id
schema_id
schema_version
evidence_type
status
subject_id
operation_id
workflow_version
policy_version
tenant_id
project_id
environment_id
capability_id
capability_contract_version
provider_id
provider_version
adapter_version
model_name/model_version
source_evidence_ids
normalized_payload
confidence/quality
reason_codes
captured_at/processed_at
duration_ms
integrity_metadata
storage_reference
retention_class
delete_after
redaction_state
supersedes/superseded_by
```

Not every evidence type requires every field. Schemas should make required provenance
explicit.

## Raw evidence and normalized evidence

### Raw evidence

Raw evidence preserves the original input or provider output when there is a justified
security, operational, legal, or review requirement.

Examples include media objects, original OCR lines, or a signed registry response.

Raw evidence is highly sensitive. It should use protected object storage, short-lived
access, strict authorization, encryption, retention limits, and audit logging.

### Normalized evidence

Normalized evidence is the stable IdentityCore representation consumed by workflows,
policies, claims, decisions, SDKs, and review tools.

For example, different OCR providers may emit different JSON, but IdentityCore stores a
common field-candidate structure with value, confidence, source lines, provider, schema,
and provenance.

Normalized evidence should not discard material uncertainty or provider-specific facts
needed for audit. Such details may be represented as versioned extensions, references,
or protected diagnostics rather than leaking into core domain fields.

## Evidence lineage

Evidence forms a directed lineage graph.

```text
Document capture
      |
      +--> Quality evidence
      +--> Classification evidence
      +--> OCR evidence
                |
                +--> Normalized name claim candidate

Selfie capture + document portrait
      |
      +--> Face-match evidence

Evidence set + policy snapshot
      |
      +--> Decision input snapshot
                |
                +--> Decision
```

Each derived record references the evidence used to produce it. Lineage enables:

- explanation;
- debugging;
- provider replacement analysis;
- model and policy impact analysis;
- deletion propagation;
- reproducibility;
- audit and compliance review.

## Evidence status

Evidence should distinguish execution state from evidentiary meaning.

Execution states may include:

```text
pending
processing
available
failed
unavailable
expired
deleted
```

Domain outcomes may include:

```text
recognized
unknown
unsupported
ambiguous
matched
not_matched
live
spoof_suspected
inconclusive
```

A provider invocation can succeed while returning an inconclusive or unsupported domain
outcome. Policies must not treat technical success as positive identity evidence.

## Confidence and quality

Confidence describes uncertainty in a result; quality describes suitability of the
input or output. They must not be treated as universal probabilities unless the provider
contract explicitly defines calibrated semantics.

Evidence should retain:

- raw score;
- score range and meaning;
- threshold used, where applicable;
- human-readable level only as a derived convenience;
- calibration/model version;
- quality issues;
- out-of-distribution or unsupported indicators.

## Integrity

Integrity controls may include:

- content hashes for stored objects;
- provider request/response signatures;
- timestamp and nonce validation;
- immutable snapshots;
- append-only audit events;
- tamper-evident audit chains;
- issuer signatures or certificate validation;
- signed exports or reports in future versions.

Integrity proves that evidence has not changed unexpectedly. It does not prove that the
original source was truthful or that a model was accurate.

## Evidence access

Access must be tenant-, environment-, role-, purpose-, and case-scoped.

Examples:

- a subject-facing session can upload evidence but cannot read internal diagnostics;
- a provider receives only the evidence required for its capability;
- a reviewer sees evidence assigned to the authorized case;
- an organization API client sees only evidence allowed by its scopes and environment;
- platform support access requires explicit privileged controls and audit.

All sensitive access should be logged. Downloads use short-lived authorization and must
not expose storage credentials or permanent object URLs.

## Retention and deletion

Evidence retention is driven by policy, evidence class, jurisdiction, purpose, legal
hold, and contractual obligations.

The lifecycle may include:

1. active processing;
2. operational retention;
3. restricted archive where justified;
4. deletion or irreversible anonymization;
5. retained minimal audit facts.

Deletion must consider descendants and copies:

- raw objects;
- normalized evidence;
- provider-side copies where contractually supported;
- cached or temporary processing files;
- exports;
- decision snapshots;
- logs and telemetry;
- backups according to documented restoration policy.

Legal holds defer deletion and record the reason. Deletion reports should state what was
deleted, anonymized, retained, and why.

## Export and redaction

Subject or tenant exports should provide understandable data while protecting:

- provider credentials;
- internal security controls;
- unrelated subjects;
- reviewer-private information where legally justified;
- raw biometric templates;
- unnecessary device/network fingerprints;
- secrets and signed evidence URLs.

Redaction must be deterministic, documented, and audited. An export is not a direct dump
of internal database or provider payloads.

## Evidence and decisions

The Decision Engine consumes a versioned evidence snapshot. The snapshot records the
specific evidence IDs, relevant values, workflow version, policy version, thresholds,
reason codes, and reviewer actions used.

Later evidence may produce a new decision or supersession, but must not rewrite the
historical inputs to an earlier decision.

## Current implementation maturity

The repository contains evidence foundations across document captures, extracted data,
biometric and liveness results, provider checks, normalized results, policy/workflow
snapshots, versioned decision inputs, Manual Review, evidence reports, audit events,
retention cleanup, legal holds, subject export, and subject deletion.

A fully generalized cross-workload evidence service and public evidence API remain areas
for consolidation. Existing domain records should progressively align to common evidence
contracts without forcing a risky one-time rewrite.

## Related documentation

- [Canonical Architecture](../../ARCHITECTURE.md)
- [Provider Runtime](provider-runtime.md)
- [Capability Model](capability-model.md)
- [Claims Engine](claims-engine.md)
