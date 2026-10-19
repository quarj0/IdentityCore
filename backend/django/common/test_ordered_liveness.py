from copy import deepcopy
from itertools import product

from django.test import SimpleTestCase

from shared.liveness_challenge import (
    ACTIONS,
    PROTOCOL,
    infer_ordered_actions,
    new_actions,
    valid_actions,
    validate_result,
)


class OrderedLivenessContractTests(SimpleTestCase):
    actions = [
        "turn_left",
        "look_up",
        "turn_right",
        "look_down",
        "turn_left",
        "look_up",
        "turn_right",
        "look_down",
    ]

    def result(self):
        return {
            "passed": True,
            "challenge_id": "lch_current",
            "challenge_protocol": PROTOCOL,
            "challenge_passed": True,
            "metrics": {
                "challenge_actions": self.actions,
                "detected_actions": self.actions,
            },
        }

    def test_motion_retains_order_revisits_and_ignores_returns_to_neutral(self):
        neutral = (0.5, 0.5)
        centers = [
            neutral,
            (0.6, 0.5),
            (0.61, 0.5),
            neutral,
            (0.5, 0.4),
            neutral,
            (0.4, 0.5),
            neutral,
            (0.5, 0.6),
            neutral,
            (0.6, 0.5),
            neutral,
        ]
        self.assertEqual(infer_ordered_actions(centers), self.actions[:5])
        self.assertEqual(infer_ordered_actions([neutral, (float("nan"), 0.5)]), [])

    def test_generic_all_directions_recording_cannot_satisfy_any_issued_sequence(self):
        generic = ["turn_left", "look_up", "turn_right", "look_down"]
        count = 0
        for actions in product(ACTIONS, repeat=8):
            actions = list(actions)
            if not valid_actions(actions):
                continue
            count += 1
            result = self.result()
            result["metrics"] = {
                "challenge_actions": actions,
                "detected_actions": generic,
            }
            with self.assertRaises(ValueError):
                validate_result(result, challenge_id="lch_current", actions=actions)
        self.assertEqual(count, 8748)

    def test_binding_rejects_wrong_order_extra_actions_old_ids_and_legacy_evidence(
        self,
    ):
        validate_result(self.result(), challenge_id="lch_current", actions=self.actions)
        for changes in (
            {"challenge_id": "lch_previous"},
            {"challenge_protocol": "unordered"},
            {"challenge_passed": False},
            {"challenge_passed": "true"},
            {"passed": "false"},
            {
                "metrics": {
                    "challenge_actions": self.actions,
                    "detected_actions": list(reversed(self.actions[1:]))
                    + self.actions[:1],
                }
            },
            {
                "metrics": {
                    "challenge_actions": self.actions,
                    "detected_actions": self.actions + ["look_up"],
                }
            },
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_result(
                    {**deepcopy(self.result()), **changes},
                    challenge_id="lch_current",
                    actions=self.actions,
                )
        with self.assertRaises(ValueError):
            validate_result(
                self.result(), challenge_id="lch_current", actions=self.actions[:2]
            )

    def test_failed_sequence_can_be_retained_but_never_claim_success(self):
        result = self.result()
        result.update(passed=False, challenge_passed=False)
        result["metrics"] = {"challenge_actions": self.actions, "detected_actions": []}
        validate_result(result, challenge_id="lch_current", actions=self.actions)

    def test_issuer_excludes_legacy_short_and_adjacent_duplicate_sequences(self):
        self.assertTrue(valid_actions(new_actions()))
        self.assertFalse(valid_actions(["turn_left", "look_up"]))
        self.assertFalse(valid_actions(["turn_left"] * 5))
