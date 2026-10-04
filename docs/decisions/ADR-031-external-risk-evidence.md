# ADR-031: External risk providers return evidence only

Status: Accepted

External risk capability v1 runs through existing provider orchestration, environment configuration, bounded attempts, circuit state and provider-check lineage. Policy snapshots explicitly opt in, set a review-score threshold and choose manual review (default) or ignore for unavailable/inconclusive evidence.

Inputs are an allowlist of evidence-presence booleans and liveness/face-match statuses, plus input version 1. No subject/verification identifiers, OCR fields, raw media, names, contact data or device/network identifiers are transmitted. This capability evaluates existing evidence sufficiency and consistency; a deployment needing additional attributes requires a separately reviewed contract version and privacy inventory change.

Outputs include provider version, risk version 1, a finite score in [0,100], and bounded known signal codes. Unknown fields (including a direct decision), versions, signals, or scores fail closed before result persistence. External scores cannot lower the local risk score or reverse local rejection/review. Elevated scores or signals request review; a favorable score supplies evidence while local policy independently determines eligibility.

Provider route exhaustion for this evidence-only call records failed attempts without writing a system decision or emitting completion events. Local risk assessment applies the snapshotted failure policy and the existing decision revision/human guard. Both external provider evidence and the internal policy assessment have their own provider checks and enter immutable decision inputs.
