# ADR 054: Ordered and bound active-liveness evidence

Status: Accepted

Unordered set membership let one all-directions recording satisfy every issued
challenge. Active liveness now issues eight unpredictable nonadjacent-repeated
directions and compares the complete observed sequence, preserving order and
revisits. The provider binds its result to the challenge ID and `ordered_motion_v1`;
worker finalization validates fresh and recovered evidence before accepting success.

The browser supplies an initial neutral hold. Direction inference uses dominant
displacement from that anchor, ignoring returns to neutral. A five-challenge budget
per verification includes replacement sessions and handoffs and is serialized under
the existing verification lock. Active sampling is bounded at 48 frames.

No schema change or historical decision rewrite is required. Old short challenges
and unbound in-flight results fail closed; deployment must coordinate capture and
processing components. The finite sequence space and motion approximation do not
establish camera attestation or certified presentation-attack resistance. See the
[contract, rollout and evaluation limits](../operations/active-liveness.md).
