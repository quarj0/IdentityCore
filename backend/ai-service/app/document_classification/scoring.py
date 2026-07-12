from __future__ import annotations

from dataclasses import dataclass

from .models import ClassificationScoringConfig


@dataclass(frozen=True)
class CandidateScore:
    required_group_coverage: float
    required_evidence_score: float
    optional_evidence_score: float
    structural_evidence_score: float
    average_ocr_confidence: float
    negative_evidence_penalty: float
    score: float


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def combine_scores(
    *,
    required_group_coverage: float,
    required_evidence_score: float,
    optional_evidence_score: float,
    structural_evidence_score: float,
    average_ocr_confidence: float,
    negative_evidence_penalty: float,
    config: ClassificationScoringConfig,
) -> CandidateScore:
    score = (
        required_evidence_score * config.required_evidence_weight
        + optional_evidence_score * config.optional_evidence_weight
        + structural_evidence_score * config.structural_evidence_weight
        + average_ocr_confidence * config.ocr_quality_weight
        - negative_evidence_penalty * config.negative_evidence_weight
    )
    return CandidateScore(
        required_group_coverage=clamp(required_group_coverage),
        required_evidence_score=clamp(required_evidence_score),
        optional_evidence_score=clamp(optional_evidence_score),
        structural_evidence_score=clamp(structural_evidence_score),
        average_ocr_confidence=clamp(average_ocr_confidence),
        negative_evidence_penalty=clamp(negative_evidence_penalty),
        score=clamp(score),
    )
