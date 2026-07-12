from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class OCRLine:
    text: str
    normalized_text: str
    confidence: float | None = None


@dataclass(frozen=True)
class PhraseRule:
    phrase: str
    weight: float = 1.0


@dataclass(frozen=True)
class PatternRule:
    pattern_id: str
    pattern: str
    weight: float = 1.0


@dataclass(frozen=True)
class DocumentDefinition:
    definition_id: str
    document_type: str
    country_code: str | None
    languages: tuple[str, ...]
    required_phrase_groups: tuple[tuple[str, ...], ...]
    optional_phrases: tuple[PhraseRule, ...] = ()
    negative_phrases: tuple[PhraseRule, ...] = ()
    structural_patterns: tuple[PatternRule, ...] = ()
    version: str = "1"
    status: str = "verified"
    enabled: bool = True
    source_notes: str = ""


@dataclass(frozen=True)
class DocumentClassificationPolicy:
    minimum_candidate_evidence: float = 0.55
    minimum_required_group_coverage: float = 0.5
    minimum_classification_margin: float = 0.08
    minimum_average_ocr_confidence: float = 0.35


@dataclass(frozen=True)
class ClassificationScoringConfig:
    required_evidence_weight: float = 0.55
    optional_evidence_weight: float = 0.10
    structural_evidence_weight: float = 0.20
    ocr_quality_weight: float = 0.10
    negative_evidence_weight: float = 0.20


class ClassificationWorkflowAction(str, Enum):
    CONTINUE = "continue"
    CONTINUE_WITH_REVIEW = "continue_with_review"
    RETRY_OR_MANUAL_REVIEW = "retry_or_manual_review"


class AIClassificationRecommendation(str, Enum):
    CONTINUE = "continue"
    CONTINUE_WITH_REVIEW = "continue_with_review"
    FAIL_CLOSED = "fail_closed"
    RETRY_REQUIRED = "retry_required"


class AIClassificationDecisionMode(str, Enum):
    FULLY_AUTOMATED = "fully_automated"
    REVIEW_SUPPORTED = "review_supported"
    PLATFORM_ADMIN = "platform_admin"
