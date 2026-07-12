from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rapidfuzz import fuzz

from .models import OCRLine
from .normalization import normalize_text

_GENERIC_TERMS = {
    "ID",
    "CARD",
    "IDENTITY",
    "REPUBLIC",
    "MEMBER",
    "GH",
}

MINIMUM_FUZZY_SIMILARITY = 0.70
MINIMUM_PARTIAL_LENGTH_RATIO = 0.65
MAXIMUM_LINE_WINDOW = 3


@dataclass(frozen=True)
class PhraseMatch:
    expected_phrase: str
    matched_text: str
    similarity_score: float
    ocr_confidence: float | None
    combined_evidence_score: float
    match_type: str
    matched_line_indexes: tuple[int, ...]


def _chunk_lines(
    lines: list[OCRLine],
    max_window: int = MAXIMUM_LINE_WINDOW,
) -> Iterable[tuple[tuple[int, ...], str, float | None]]:
    for start in range(len(lines)):
        for end in range(
            start + 1,
            min(len(lines), start + max_window) + 1,
        ):
            window = lines[start:end]

            text = " ".join(
                line.normalized_text for line in window if line.normalized_text
            ).strip()

            if not text:
                continue

            confidences = [
                line.confidence for line in window if line.confidence is not None
            ]

            average_confidence = (
                sum(confidences) / len(confidences) if confidences else None
            )

            yield (
                tuple(range(start, end)),
                text,
                average_confidence,
            )


def _calculate_similarity(
    expected: str,
    candidate: str,
) -> float:
    direct_score = fuzz.ratio(expected, candidate) / 100.0

    maximum_length = max(len(expected), len(candidate))
    if maximum_length == 0:
        return 0.0

    length_ratio = min(len(expected), len(candidate)) / maximum_length

    if length_ratio < MINIMUM_PARTIAL_LENGTH_RATIO:
        return direct_score

    partial_score = fuzz.partial_ratio(expected, candidate) / 100.0
    return max(direct_score, partial_score)


def phrase_match(
    expected_phrase: str,
    lines: list[OCRLine],
) -> PhraseMatch | None:
    normalized_phrase = normalize_text(expected_phrase)

    if not normalized_phrase:
        return None

    phrase_tokens = normalized_phrase.split()

    if len(phrase_tokens) <= 1 and normalized_phrase in _GENERIC_TERMS:
        return None

    best_match: PhraseMatch | None = None

    for indexes, candidate_text, candidate_confidence in _chunk_lines(lines):
        if normalized_phrase == candidate_text:
            similarity = 1.0
            match_type = "exact"
        else:
            similarity = _calculate_similarity(
                normalized_phrase,
                candidate_text,
            )

            if similarity < MINIMUM_FUZZY_SIMILARITY:
                continue

            match_type = "fuzzy"

        combined_evidence = (
            similarity * candidate_confidence
            if candidate_confidence is not None
            else 0.0
        )

        candidate = PhraseMatch(
            expected_phrase=normalized_phrase,
            matched_text=candidate_text,
            similarity_score=round(similarity, 4),
            ocr_confidence=(
                round(candidate_confidence, 4)
                if candidate_confidence is not None
                else None
            ),
            combined_evidence_score=round(
                combined_evidence,
                4,
            ),
            match_type=match_type,
            matched_line_indexes=indexes,
        )

        if best_match is None:
            best_match = candidate
            continue

        candidate_rank = (
            candidate.combined_evidence_score,
            candidate.similarity_score,
            candidate.match_type == "exact",
        )
        current_rank = (
            best_match.combined_evidence_score,
            best_match.similarity_score,
            best_match.match_type == "exact",
        )

        if candidate_rank > current_rank:
            best_match = candidate

    return best_match
