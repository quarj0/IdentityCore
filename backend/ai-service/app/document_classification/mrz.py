from __future__ import annotations

from dataclasses import dataclass

_MRZ_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")


@dataclass(frozen=True)
class MrzEvidence:
    valid: bool
    score: float
    issuing_country: str | None
    matched_lines: tuple[str, str] | None
    reason_codes: tuple[str, ...] = ()


def _mrz_char_value(character: str) -> int:
    if character == "<":
        return 0
    if character.isdigit():
        return int(character)
    return ord(character) - 55


def _check_digit(value: str) -> str:
    weights = (7, 3, 1)
    total = 0
    for index, character in enumerate(value):
        total += _mrz_char_value(character) * weights[index % 3]
    return str(total % 10)


def _candidate_lines(lines: list[str]) -> list[str]:
    candidates: list[str] = []
    for text in lines:
        raw = "".join(character for character in text.upper() if not character.isspace())
        if raw:
            candidates.append(raw)
    return candidates


def evaluate_td3_mrz(lines: list[str]) -> MrzEvidence:
    candidates = _candidate_lines(lines)
    for first, second in zip(candidates, candidates[1:]):
        if len(first) != 44 or len(second) != 44:
            continue
        if any(character not in _MRZ_ALLOWED for character in first + second):
            continue
        if not first.startswith("P<"):
            continue
        checks = [
            second[9] == _check_digit(second[0:9]),
            second[19] == _check_digit(second[13:19]),
            second[27] == _check_digit(second[21:27]),
            second[43] == _check_digit(second[0:10] + second[13:20] + second[21:43]),
        ]
        score = 0.55 + (0.1 * sum(1 for check in checks if check))
        if all(checks):
            score = 0.95
            return MrzEvidence(
                valid=True,
                score=score,
                issuing_country=second[2:5].replace("<", "") or None,
                matched_lines=(first, second),
            )
        return MrzEvidence(
            valid=False,
            score=score,
            issuing_country=second[2:5].replace("<", "") or None,
            matched_lines=(first, second),
            reason_codes=("passport_mrz_invalid",),
        )

    return MrzEvidence(
        valid=False,
        score=0.0,
        issuing_country=None,
        matched_lines=None,
        reason_codes=("passport_mrz_invalid",),
    )
