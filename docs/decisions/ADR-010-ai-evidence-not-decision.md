# ADR-010: AI as Evidence, Not Decision

**Status:** Accepted

**Date:** 2026-07-04

---

## Context

IdentityCore uses Artificial Intelligence to assist identity verification through capabilities such as:

- Face detection
- Face matching
- Liveness detection
- Document classification
- OCR
- Document quality assessment

While AI models can produce highly accurate technical results, they are probabilistic systems.

They may produce:

- False positives
- False negatives
- Low-confidence predictions
- Inconsistent results
- Bias across document types or populations

Identity verification is a high-impact process that can affect access to services, employment, education, healthcare, and other important activities.

For these reasons, AI should support decision-making rather than replace it.

---

## Decision

IdentityCore adopts the principle:

> **Artificial Intelligence provides technical evidence. Business decisions are made by the Decision Engine.**

The AI service must never determine whether a Verification is approved or rejected.

Instead, it returns measurable technical outputs that the platform evaluates according to configurable Verification Policies.

---

## AI Responsibilities

The AI service is responsible for:

- Detecting faces
- Aligning faces
- Generating biometric embeddings
- Comparing faces
- Performing liveness checks
- Assessing document quality
- Classifying document types
- Extracting using OCR
- Returning confidence scores
- Reporting model metadata

Document classification is evidence-producing only:

- It may report `classification_status`, `workflow_action`, and manual-review evidence.
- It must not approve or reject a verification.
- Unknown, unsupported, ambiguous, or low-evidence document classifications should preserve evidence and allow the workflow engine to apply policy.

The AI service is not responsible for business decisions.

---

## Decision Engine Responsibilities

The Decision Engine is responsible for:

- Applying Verification Policies
- Evaluating AI evidence
- Applying business rules
- Considering manual review requirements
- Producing the final Verification Decision
- Recording decision rationale
- Creating Audit Events

The Decision Engine operates within the Django backend.

---

## Example Workflow

```id="t0zqg4"
Document Uploaded
        │
        ▼
AI Service

Face Match = 0.93

Liveness = 0.91

OCR Confidence = 0.98

Quality = 0.89

        │
        ▼

Decision Engine

Verification Policy

↓

Verified
```

If the same evidence falls below configured thresholds:

```id="mxudj6"
Face Match = 0.67

↓

Manual Review
```

The outcome depends on policy, not the AI model.

---

## Why This Approach?

Separating evidence from decisions provides:

- Explainability
- Auditability
- Configurable business rules
- Easier testing
- Better governance
- Regulatory flexibility
- Reduced vendor lock-in

Organizations can change business policies without changing AI models.

Likewise, AI models can be upgraded without changing business logic.

---

## Explainability

Every Verification Decision should be explainable.

Example:

```id="z8rycq"
Verification Result

Verified

Reason:

Face Match: 0.94

Liveness: Passed

OCR Confidence: 0.98

Document Quality: Acceptable

Verification Policy Version: v1.3
```

This improves trust, debugging, and compliance.

---

## Manual Review

AI uncertainty should trigger human review rather than automatic rejection where appropriate.

Examples:

- Borderline face match
- Low OCR confidence
- Inconclusive liveness
- Poor document quality
- Provider disagreement

Manual Review remains an important safety mechanism.

Document-related manual review should be triggered from the workflow engine when classification evidence is uncertain or mismatched, not from a hard AI rejection.

---

## Verification Policies

Different organizations may configure different thresholds.

Example:

University:

```id="q7vxk9"
Face Match

0.80
```

Bank:

```id="jlwmy8"
Face Match

0.95
```

The AI model remains unchanged.

Only policy changes.

---

## AI Independence

The Decision Engine should not depend on:

- Specific AI models
- Specific providers
- Specific confidence scales

The backend evaluates normalized evidence.

This allows:

- Model replacement
- Provider replacement
- Independent AI improvements

without rewriting business logic.

---

## Auditability

Every Verification should record:

- AI model
- Model version
- Confidence scores
- Verification Policy version
- Decision timestamp
- Decision rationale
- Manual reviewer, if applicable

This enables complete traceability.

---

## Security

The AI service should never receive responsibilities related to:

- Authentication
- Authorization
- Tenant isolation
- Permission enforcement
- Business policy evaluation

These remain within the trusted backend.

---

## Consequences

## Positive

- Better explainability.
- Stronger compliance.
- Easier testing.
- Easier model replacement.
- Clear separation of concerns.
- Improved auditability.
- Human oversight where appropriate.

## Negative

- Additional implementation effort.
- Decision Engine requires more business logic.
- More components participate in the verification workflow.

These trade-offs are acceptable because they produce a safer and more maintainable system.

---

## Alternatives Considered

## AI Makes Final Decisions

Rejected because:

- AI is probabilistic.
- Decisions become difficult to explain.
- Regulatory expectations often require human oversight.
- Business rules become tightly coupled to AI models.
- Organizations lose flexibility.

---

## Hardcoded AI Thresholds

Rejected because thresholds vary depending on:

- Industry
- Risk tolerance
- Organization policy
- Regulatory requirements

Thresholds belong in Verification Policies, not AI models.

---

## External Provider Controls Decision

Rejected because IdentityCore must remain the system of record.

External providers supply evidence, not authoritative business outcomes.

---

## Future Considerations

Future versions may introduce:

- Multiple AI models per verification.
- AI ensemble scoring.
- Risk-based adaptive thresholds.
- Model drift detection.
- AI explainability reports.
- Confidence calibration.
- Fraud detection models.

These enhancements should continue to support, rather than replace, the Decision Engine.

---

## Implementation Notes

- AI returns evidence.
- Django Decision Engine returns Verification Decisions.
- AI models remain replaceable.
- Verification Policies remain configurable.
- Manual Review remains available for uncertain or high-risk cases.
- Every decision must be auditable.

---

## References

- AI Design
- Architecture
- Security
- Compliance
- Testing Strategy
- ADR-004: Dedicated FastAPI AI Service
- ADR-009: Provider Adapter Pattern
