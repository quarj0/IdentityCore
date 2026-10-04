# External risk capability v1

Opt in per verification policy with `external_risk_enabled`, `external_risk_review_threshold` (0–100, default 70) and `external_risk_failure_action` (`manual_review` default or explicitly `ignore`). Settings enter the immutable verification policy snapshot. Older policies remain disabled. Configure and approve a `risk_check` route in each project environment through provider setup.

The registered adapter method is `risk_check(timeout_seconds=..., input_version="1", document_submitted=..., document_requires_manual_review=..., selfie_submitted=..., liveness_status=..., face_match_status=...)`. Configured HTTP providers receive these under the Contract v1 `inputs` object. A minimal completed response is:

```json
{"contract_version":"1","capability":"risk_check","status":"completed","risk_version":"1","provider_version":"rules-2026.10","risk_score":72,"signals":["inconsistent_evidence"]}
```

Known signals: `document_risk`, `velocity_risk`, `network_risk`, `inconsistent_evidence`. The v1 input contract deliberately omits identifying attributes and raw velocity/network data; providers may only return supported signals they can substantiate from the permitted inputs. Unavailable evidence and `status: inconclusive` with `risk_score: null` follow the snapshot's failure action. No other result fields are permitted. Provider-specific details belong in a separately reviewed contract, not a free-form reason or decision field.

The score can raise local risk but cannot erase a local rejection/review. Scores above the threshold and any declared risk signal require human review. Successful, low-risk external evidence alone cannot approve a case. Timeouts, malformed contracts and exhausted routes remain observable provider checks and enter review by default. Retain external provider version/check lineage in encrypted assessment and decision evidence. See ADR-031.
