from __future__ import annotations

from typing import Any

from .matching import phrase_match
from .models import (
    AIClassificationDecisionMode,
    AIClassificationRecommendation,
    ClassificationScoringConfig,
    DocumentClassificationPolicy,
    ClassificationWorkflowAction,
    OCRLine,
    DocumentDefinition,
)
from .mrz import evaluate_td3_mrz
from .normalization import normalize_text
from .registry import list_definitions
from .scoring import combine_scores


def _get_settings():
    try:
        from app.settings import get_settings

        return get_settings()
    except ModuleNotFoundError:
        class _FallbackSettings:
            document_classification_policy = DocumentClassificationPolicy()
            document_classification_scoring_config = ClassificationScoringConfig()

        return _FallbackSettings()


def build_ocr_lines(texts: list[str], scores: list[float]) -> tuple[OCRLine, ...]:
    ocr_lines: list[OCRLine] = []
    for index, text in enumerate(texts):
        normalized_text = normalize_text(text)
        if not normalized_text:
            continue
        confidence: float | None = None
        if index < len(scores):
            confidence = max(0.0, min(1.0, float(scores[index])))
        ocr_lines.append(
            OCRLine(
                text=text,
                normalized_text=normalized_text,
                confidence=confidence,
            )
        )
    return tuple(ocr_lines)


def _average_confidence(lines: tuple[OCRLine, ...]) -> float:
    confidences = [line.confidence for line in lines if line.confidence is not None]
    return sum(confidences) / len(confidences) if confidences else 0.0


def _score_definition(
    definition: DocumentDefinition,
    lines: tuple[OCRLine, ...],
    *,
    config: ClassificationScoringConfig,
) -> dict[str, Any]:
    required_group_matches: list[dict[str, Any]] = []
    matched_lines: set[int] = set()
    for group in definition.required_phrase_groups:
        best_group_match = None
        for phrase in group:
            candidate_match = phrase_match(phrase, list(lines))
            if candidate_match is None:
                continue
            if best_group_match is None or candidate_match.combined_evidence_score > best_group_match["combined_evidence_score"]:
                best_group_match = {
                    "expected_phrase": candidate_match.expected_phrase,
                    "matched_text": candidate_match.matched_text,
                    "similarity_score": candidate_match.similarity_score,
                    "ocr_confidence": candidate_match.ocr_confidence,
                    "combined_evidence_score": candidate_match.combined_evidence_score,
                    "match_type": candidate_match.match_type,
                    "matched_line_indexes": candidate_match.matched_line_indexes,
                }
        if best_group_match is not None:
            required_group_matches.append(best_group_match)
            matched_lines.update(best_group_match["matched_line_indexes"])

    optional_matches: list[dict[str, Any]] = []
    for phrase_rule in definition.optional_phrases:
        candidate_match = phrase_match(phrase_rule.phrase, list(lines))
        if candidate_match is not None:
            optional_matches.append(
                {
                    "expected_phrase": candidate_match.expected_phrase,
                    "matched_text": candidate_match.matched_text,
                    "similarity_score": candidate_match.similarity_score,
                    "ocr_confidence": candidate_match.ocr_confidence,
                    "combined_evidence_score": round(
                        candidate_match.combined_evidence_score * phrase_rule.weight, 4
                    ),
                    "match_type": candidate_match.match_type,
                    "matched_line_indexes": candidate_match.matched_line_indexes,
                }
            )

    negative_matches: list[dict[str, Any]] = []
    for phrase_rule in definition.negative_phrases:
        candidate_match = phrase_match(phrase_rule.phrase, list(lines))
        if candidate_match is not None:
            negative_matches.append(
                {
                    "expected_phrase": candidate_match.expected_phrase,
                    "matched_text": candidate_match.matched_text,
                    "similarity_score": candidate_match.similarity_score,
                    "ocr_confidence": candidate_match.ocr_confidence,
                    "combined_evidence_score": round(
                        candidate_match.combined_evidence_score * phrase_rule.weight, 4
                    ),
                    "match_type": candidate_match.match_type,
                    "matched_line_indexes": candidate_match.matched_line_indexes,
                }
            )

    structural_score = 0.0
    structural_evidence: list[dict[str, Any]] = []
    if definition.document_type == "passport":
        mrz_evidence = evaluate_td3_mrz([line.text for line in lines])
        structural_score = mrz_evidence.score
        structural_evidence.append(
            {
                "pattern_id": "td3_mrz",
                "valid": mrz_evidence.valid,
                "score": round(mrz_evidence.score, 4),
                "issuing_country": mrz_evidence.issuing_country,
                "reason_codes": list(mrz_evidence.reason_codes),
            }
        )
        if not mrz_evidence.valid:
            structural_score = 0.0

    required_group_coverage = (
        len(required_group_matches) / len(definition.required_phrase_groups)
        if definition.required_phrase_groups
        else 0.0
    )
    required_evidence_score = (
        sum(match["combined_evidence_score"] for match in required_group_matches)
        / len(required_group_matches)
        if required_group_matches
        else 0.0
    )
    optional_evidence_score = (
        sum(match["combined_evidence_score"] for match in optional_matches) / len(optional_matches)
        if optional_matches
        else 0.0
    )
    negative_penalty = (
        sum(match["combined_evidence_score"] for match in negative_matches) / len(negative_matches)
        if negative_matches
        else 0.0
    )
    average_ocr_confidence = _average_confidence(lines)

    score = combine_scores(
        required_group_coverage=required_group_coverage,
        required_evidence_score=required_evidence_score,
        optional_evidence_score=optional_evidence_score,
        structural_evidence_score=structural_score,
        average_ocr_confidence=average_ocr_confidence,
        negative_evidence_penalty=negative_penalty,
        config=config,
    )
    evidence_items: list[dict[str, Any]] = []
    if required_group_matches:
        evidence_items.append({"type": "required_phrases", "items": required_group_matches})
    if optional_matches:
        evidence_items.append({"type": "optional_phrases", "items": optional_matches})
    if structural_evidence:
        evidence_items.append({"type": "structural", "items": structural_evidence})
    if negative_matches:
        evidence_items.append({"type": "negative_phrases", "items": negative_matches})

    return {
        "definition": definition,
        "score": score,
        "evidence": evidence_items,
        "matched_lines": sorted(matched_lines),
        "structural_evidence": structural_evidence,
        "average_ocr_confidence": average_ocr_confidence,
    }


def _recommendation_for_status(
    status: str,
    matched_expected_document_type: bool | None,
    decision_mode: AIClassificationDecisionMode,
) -> AIClassificationRecommendation:
    if status == "processing_failed":
        return AIClassificationRecommendation.RETRY_REQUIRED
    if decision_mode == AIClassificationDecisionMode.FULLY_AUTOMATED:
        return (
            AIClassificationRecommendation.CONTINUE
            if status == "recognized" and matched_expected_document_type is True
            else AIClassificationRecommendation.FAIL_CLOSED
        )
    if decision_mode == AIClassificationDecisionMode.PLATFORM_ADMIN:
        return (
            AIClassificationRecommendation.CONTINUE
            if status == "recognized" and matched_expected_document_type is True
            else AIClassificationRecommendation.FAIL_CLOSED
        )
    return (
        AIClassificationRecommendation.CONTINUE
        if status == "recognized" and matched_expected_document_type is True
        else AIClassificationRecommendation.CONTINUE_WITH_REVIEW
    )


def classify_document(
    lines: tuple[OCRLine, ...],
    *,
    expected_document_type: str,
    country_code: str,
    decision_mode: AIClassificationDecisionMode = AIClassificationDecisionMode.REVIEW_SUPPORTED,
    scoring_config: ClassificationScoringConfig | None = None,
) -> dict[str, Any]:
    settings = _get_settings()
    scoring_config = scoring_config or settings.document_classification_scoring_config
    policy = settings.document_classification_policy
    applicable_definitions = list_definitions(country_code or None)
    if not applicable_definitions:
        return {
            "classification_status": "unsupported",
            "predicted_document_type": "unknown",
            "predicted_country_code": None,
            "expected_document_type": expected_document_type,
            "matched_expected_document_type": None,
            "confidence_score": 0.0,
            "evidence_score": 0.0,
            "classification_margin": 0.0,
            "workflow_action": ClassificationWorkflowAction.CONTINUE_WITH_REVIEW.value,
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "high",
                "reason_codes": ["unsupported_country_document_definition"],
                "review_category": "document_classification",
            },
            "issues": ["unsupported_country_document_definition"],
            "ocr": {
                "average_confidence": round(_average_confidence(lines), 4),
                "line_count": len(lines),
            },
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [line.text for line in lines],
            "score_components": {},
            "classifier": {
                "name": "ocr-evidence-document-classifier",
                "version": "v2",
                "score_type": "uncalibrated_evidence_score",
            },
            "ocr_model": {
                "name": "paddleocr",
                "version": "PP-OCRv5",
            },
            "recommendation": _recommendation_for_status(
                "unsupported", None, decision_mode
            ).value,
        }

    candidates: list[dict[str, Any]] = []
    skipped_issues: list[str] = []
    for definition in applicable_definitions:
        scored = _score_definition(definition, lines, config=scoring_config)
        candidate_score = scored["score"]
        has_valid_passport_mrz = (
            definition.document_type == "passport"
            and any(item.get("valid") for item in scored["structural_evidence"])
        )
        if definition.document_type == "passport" and not has_valid_passport_mrz:
            skipped_issues.append("passport_mrz_invalid")
            continue
        # A checksum-valid TD3 MRZ is stronger structural evidence than weak or
        # localized visible wording, so it may independently identify a passport.
        if (
            candidate_score.score < policy.minimum_candidate_evidence
            and not has_valid_passport_mrz
        ):
            continue
        if (
            scored["definition"].required_phrase_groups
            and candidate_score.required_group_coverage
            < policy.minimum_required_group_coverage
            and not has_valid_passport_mrz
        ):
            continue
        candidates.append(
            {
                "definition_id": definition.definition_id,
                "document_type": definition.document_type,
                "country_code": definition.country_code,
                "score": round(candidate_score.score, 4),
                "required_group_coverage": round(candidate_score.required_group_coverage, 4),
                "required_evidence_score": round(candidate_score.required_evidence_score, 4),
                "optional_evidence_score": round(candidate_score.optional_evidence_score, 4),
                "structural_evidence_score": round(candidate_score.structural_evidence_score, 4),
                "average_ocr_confidence": round(candidate_score.average_ocr_confidence, 4),
                "negative_evidence_penalty": round(candidate_score.negative_evidence_penalty, 4),
                "evidence": scored["evidence"],
                "structural_evidence": scored["structural_evidence"],
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    average_confidence = round(_average_confidence(lines), 4)
    if not candidates:
        status = "insufficient_evidence" if average_confidence < policy.minimum_average_ocr_confidence else "unknown"
        issue = "ocr_confidence_too_low" if status == "insufficient_evidence" else "document_type_not_determined"
        if (
            expected_document_type == "passport"
            and "passport_mrz_invalid" in skipped_issues
        ):
            issue = "passport_mrz_invalid"
            status = "unknown"
        return {
            "classification_status": status,
            "predicted_document_type": "unknown",
            "predicted_country_code": None,
            "expected_document_type": expected_document_type,
            "matched_expected_document_type": None,
            "confidence_score": 0.0,
            "evidence_score": 0.0,
            "classification_margin": 0.0,
            "workflow_action": ClassificationWorkflowAction.CONTINUE_WITH_REVIEW.value,
            "requires_manual_review": True,
            "manual_review": {
                "required": True,
                "priority": "high" if status == "insufficient_evidence" else "normal",
                "reason_codes": [issue],
                "review_category": "document_classification",
            },
            "issues": [issue],
            "ocr": {
                "average_confidence": average_confidence,
                "line_count": len(lines),
            },
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [line.text for line in lines],
            "score_components": {},
            "classifier": {
                "name": "ocr-evidence-document-classifier",
                "version": "v2",
                "score_type": "uncalibrated_evidence_score",
            },
            "ocr_model": {
                "name": "paddleocr",
                "version": "PP-OCRv5",
            },
            "recommendation": _recommendation_for_status(status, None, decision_mode).value,
        }

    top_candidate = candidates[0]
    second_candidate = candidates[1] if len(candidates) > 1 else None
    margin = round(top_candidate["score"] - second_candidate["score"], 4) if second_candidate else 1.0

    if second_candidate is not None and margin < policy.minimum_classification_margin:
        status = "ambiguous"
        predicted_type = "unknown"
        matched_expected_document_type = None
        issues = ["document_classification_ambiguous"]
        manual_review_priority = "high"
    else:
        status = "recognized"
        predicted_type = top_candidate["document_type"]
        matched_expected_document_type = predicted_type == expected_document_type
        if matched_expected_document_type:
            issues = []
            manual_review_priority = "low"
        else:
            issues = ["document_type_mismatch"]
            manual_review_priority = "high"

    requires_manual_review = status != "recognized" or matched_expected_document_type is False
    workflow_action = (
        ClassificationWorkflowAction.CONTINUE.value
        if status == "recognized" and matched_expected_document_type is True
        else ClassificationWorkflowAction.CONTINUE_WITH_REVIEW.value
    )

    if status == "recognized" and matched_expected_document_type is False:
        issues = ["document_type_mismatch"]

    manual_review = {
        "required": requires_manual_review,
        "priority": manual_review_priority if requires_manual_review else "low",
        "reason_codes": issues if requires_manual_review else [],
        "review_category": "document_classification",
    }

    result = {
        "classification_status": status,
        "predicted_document_type": predicted_type,
        "predicted_country_code": top_candidate["country_code"] if status == "recognized" else None,
        "expected_document_type": expected_document_type,
        "matched_expected_document_type": matched_expected_document_type,
        "confidence_score": round(top_candidate["score"], 4),
        "evidence_score": round(top_candidate["score"], 4),
        "classification_margin": margin,
        "workflow_action": workflow_action,
        "requires_manual_review": requires_manual_review,
        "manual_review": manual_review,
        "issues": issues,
        "ocr": {
            "average_confidence": average_confidence,
            "line_count": len(lines),
            "lines": [
                {
                    "text": line.text,
                    "normalized_text": line.normalized_text,
                    "confidence": line.confidence,
                }
                for line in lines
            ],
        },
        "score_components": {
            "required_group_coverage": round(top_candidate["required_group_coverage"], 4),
            "required_evidence_score": round(top_candidate["required_evidence_score"], 4),
            "optional_evidence_score": round(top_candidate["optional_evidence_score"], 4),
            "structural_evidence_score": round(top_candidate["structural_evidence_score"], 4),
            "average_ocr_confidence": round(top_candidate["average_ocr_confidence"], 4),
            "negative_evidence_penalty": round(top_candidate["negative_evidence_penalty"], 4),
        },
        "evidence": top_candidate["evidence"],
        "candidates": candidates,
        "raw_text_lines": [line.text for line in lines],
        "classifier": {
            "name": "ocr-evidence-document-classifier",
            "version": "v2",
            "score_type": "uncalibrated_evidence_score",
        },
        "ocr_model": {
            "name": "paddleocr",
            "version": "PP-OCRv5",
        },
        "recommendation": _recommendation_for_status(status, matched_expected_document_type, decision_mode).value,
    }
    return result
