"""Ordered motion contract shared by challenge issuance and provider validation.

Motion checks are one signal alongside PAD, not proof of camera provenance.
"""

import math
import secrets

PROTOCOL = "ordered_motion_v1"
ACTIONS = ("turn_left", "turn_right", "look_up", "look_down")
ACTION_COUNT = 8
MAX_CHALLENGES = 5


def new_actions():
    actions = []
    for _ in range(ACTION_COUNT):
        actions.append(
            secrets.choice(
                [value for value in ACTIONS if not actions or value != actions[-1]]
            )
        )
    return actions


def valid_actions(actions):
    return (
        isinstance(actions, list)
        and len(actions) == ACTION_COUNT
        and all(isinstance(value, str) and value in ACTIONS for value in actions)
        and all(left != right for left, right in zip(actions, actions[1:]))
    )


def infer_ordered_actions(centers, *, movement_threshold=0.03):
    """Measure dominant displacement from initial neutral position.

    Returning to neutral is not the opposite action. Only adjacent repetitions
    are collapsed; revisiting a direction later in the recording is retained.
    """
    if not centers:
        return []
    anchor_x, anchor_y = centers[0]
    actions = []
    previous = None
    for x, y in centers[1:]:
        if not all(math.isfinite(value) for value in (x, y, anchor_x, anchor_y)):
            return []
        dx, dy = x - anchor_x, y - anchor_y
        if max(abs(dx), abs(dy)) < movement_threshold:
            previous = None
            continue
        if abs(dx) >= abs(dy):
            # The portal mirrors only its preview. Provider pixels are unmirrored;
            # applicant-left therefore moves toward the right of the raw frame.
            action = "turn_left" if dx > 0 else "turn_right"
        else:
            action = "look_down" if dy > 0 else "look_up"
        if action != previous:
            actions.append(action)
        previous = action
    return actions


def validate_result(result, *, challenge_id, actions):
    """Reject unbound, legacy or contradictory active provider evidence."""
    if not isinstance(result.get("passed"), bool):
        raise ValueError("Active liveness outcome must be boolean.")
    if not challenge_id or not valid_actions(actions):
        raise ValueError("A current ordered active challenge is required.")
    if (
        result.get("challenge_id") != challenge_id
        or result.get("challenge_protocol") != PROTOCOL
    ):
        raise ValueError("Active evidence must bind the issued challenge and protocol.")
    metrics = result.get("metrics")
    if not isinstance(metrics, dict) or metrics.get("challenge_actions") != actions:
        raise ValueError("Active evidence must bind the exact requested sequence.")
    observed = metrics.get("detected_actions")
    if (
        not isinstance(observed, list)
        or len(observed) > 64
        or any(not isinstance(value, str) or value not in ACTIONS for value in observed)
    ):
        raise ValueError("Active evidence must include bounded ordered observations.")
    matched = result.get("challenge_passed")
    if not isinstance(matched, bool) or (matched and observed != actions):
        raise ValueError(
            "Active challenge success requires the exact observed sequence."
        )
    if result.get("passed") and not matched:
        raise ValueError("Active liveness cannot pass an incomplete challenge.")
