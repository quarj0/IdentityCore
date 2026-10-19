# Ordered active liveness

Active checks use `ordered_motion_v1`. The server issues eight cryptographically
random directions with no adjacent repeats, drawn from `turn_left`, `turn_right`,
`look_up`, `look_down`. The sequence has 8,748 possible values. Challenges expire
at the earlier of three minutes or session expiry and remain single-use. A case
can issue at most five challenges across all sessions and mobile handoffs; retained
soft-deleted challenges count. The verification row lock serializes issuance.
When exhausted, the requesting organization must restart verification in a new case.

The portal records an initial one-second neutral hold, then eight 2.2-second prompts
and a 1.2-second tail (about 20 seconds, with a 22-second hard stop). The initial
neutral position anchors dominant face-center displacement. Directions are from the
applicant's perspective; only the preview is mirrored. Returning to neutral is not
counted as the opposite direction. Revisited directions remain in the observed
sequence. Active video uses at most 48 sampled frames; passive processing retains
its configured sample limit. Low quality or incomplete observations fail safely.

## Provider contract

Active provider input includes `challenge_id`, `challenge_protocol` and the exact
ordered `challenge_actions`. The response must echo that ID/protocol and include:

```json
{
  "passed": true,
  "challenge_id": "lch_issued_id",
  "challenge_protocol": "ordered_motion_v1",
  "challenge_passed": true,
  "metrics": {
    "face_count": 1,
    "avg_detection_confidence": 0.97,
    "challenge_actions": ["turn_left", "look_up", "turn_right", "look_down", "turn_left", "look_up", "turn_right", "look_down"],
    "detected_actions": ["turn_left", "look_up", "turn_right", "look_down", "turn_left", "look_up", "turn_right", "look_down"]
  },
  "model_name": "provider-model",
  "model_version": "provider-version"
}
```

Ordinary score, confidence and provider-envelope requirements also apply. Success
requires exact sequence equality, including order and repeated directions. Extra
movements or a recording containing all directions do not satisfy arbitrary
challenges. A claimed success with missing binding, false/nonboolean challenge
success or contradictory observations is invalid provider evidence and routes to
manual review. Cached and recovered results receive the same validation. A valid
failed challenge can be retained as failed evidence.

## Deployment and limits

Pause active capture, drain in-flight processing, then coordinate the AI service,
workers, API and portal upgrade. Old short challenges must be replaced and recorded
again. Legacy or unbound in-flight active results cannot become a new passed check.
Completed historical checks and decisions are not rewritten. There is no schema
migration. BYOP active providers must implement this sub-contract before activation;
legacy bearer/signed transport choices do not relax evidence validation.

This closes unordered membership matching; it is not physical-camera attestation
or replay-proof certification. The finite sequence space and retry cap limit
challenge fishing; PAD, server-owned consent, upload receipts and retained-media
reuse signals remain independent controls. A modified browser, virtual camera or
adaptive generated video still requires representative adversarial evaluation.
Face-center motion is an approximation, not a calibrated head-pose model. Validate
physical-device capture, sampling, movement thresholds, accessibility and false
accept/reject rates before production claims. Mock mode and synthetic geometry
regressions establish contract behavior only.
