from decimal import Decimal

from django.utils import timezone

from apps.biometrics.models import FaceMatchStatus, LivenessCheckStatus
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.providers.services import create_provider_check
from apps.risk.models import RiskAssessment, RiskLevel, RiskRecommendation
from apps.verifications.models import (
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)


def _get_policy_thresholds(verification) -> tuple[Decimal, Decimal]:
    snapshot = verification.policy_snapshot_json or {}
    face_match_threshold = Decimal(str(snapshot.get("face_match_threshold", "0.8500")))
    manual_review_threshold = Decimal(
        str(snapshot.get("manual_review_threshold", "0.6500"))
    )
    return face_match_threshold, manual_review_threshold


def evaluate_risk_assessment(verification) -> RiskAssessment:
    latest_liveness_check = verification.liveness_checks.order_by("-checked_at").first()
    latest_face_match = verification.face_matches.order_by("-matched_at").first()
    latest_identity_document = verification.identity_documents.order_by("-created_at").first()
    document_classification = (
        (latest_identity_document.extracted_data_json or {}).get("document_classification")
        if latest_identity_document is not None
        else None
    )
    face_match_threshold, manual_review_threshold = _get_policy_thresholds(verification)

    signals = {
        "document_submitted": verification.identity_documents.exists(),
        "document_classification": document_classification,
        "selfie_submitted": verification.selfie_captures.exists(),
        "liveness_status": (
            latest_liveness_check.status if latest_liveness_check else "missing"
        ),
        "liveness_score": (
            float(latest_liveness_check.score)
            if latest_liveness_check and latest_liveness_check.score is not None
            else None
        ),
        "face_match_status": (
            latest_face_match.status if latest_face_match else "missing"
        ),
        "face_match_score": (
            float(latest_face_match.match_score)
            if latest_face_match and latest_face_match.match_score is not None
            else None
        ),
        "thresholds": {
            "face_match": float(face_match_threshold),
            "manual_review": float(manual_review_threshold),
        },
    }

    if latest_liveness_check is None or latest_face_match is None:
        risk_score = Decimal("95.00")
        risk_level = RiskLevel.CRITICAL
        recommendation = RiskRecommendation.MANUAL_REVIEW
    elif latest_liveness_check.status in {
        LivenessCheckStatus.FAILED,
        LivenessCheckStatus.ERROR,
    }:
        risk_score = Decimal("96.00")
        risk_level = RiskLevel.CRITICAL
        recommendation = RiskRecommendation.REJECT
    elif latest_face_match.status == FaceMatchStatus.ERROR:
        risk_score = Decimal("82.00")
        risk_level = RiskLevel.HIGH
        recommendation = RiskRecommendation.MANUAL_REVIEW
    elif latest_liveness_check.status == LivenessCheckStatus.INCONCLUSIVE:
        risk_score = Decimal("78.00")
        risk_level = RiskLevel.HIGH
        recommendation = RiskRecommendation.MANUAL_REVIEW
    elif latest_face_match.status == FaceMatchStatus.INCONCLUSIVE:
        risk_score = Decimal("74.00")
        risk_level = RiskLevel.HIGH
        recommendation = RiskRecommendation.MANUAL_REVIEW
    elif latest_face_match.status == FaceMatchStatus.NOT_MATCHED:
        face_score = latest_face_match.match_score or Decimal("0")
        if face_score < manual_review_threshold:
            risk_score = Decimal("91.00")
            risk_level = RiskLevel.CRITICAL
            recommendation = RiskRecommendation.REJECT
        else:
            risk_score = Decimal("68.00")
            risk_level = RiskLevel.MEDIUM
            recommendation = RiskRecommendation.MANUAL_REVIEW
    else:
        face_score = latest_face_match.match_score or Decimal("0")
        if (
            latest_liveness_check.status == LivenessCheckStatus.PASSED
            and face_score >= face_match_threshold
        ):
            risk_score = Decimal("14.00")
            risk_level = RiskLevel.LOW
            recommendation = RiskRecommendation.APPROVE
        else:
            risk_score = Decimal("58.00")
            risk_level = RiskLevel.MEDIUM
            recommendation = RiskRecommendation.MANUAL_REVIEW

    create_provider_check(
        verification=verification,
        check_type=ProviderCheckType.RISK_CHECK,
        status=ProviderCheckStatus.COMPLETED,
        normalized_result={
            "risk_level": risk_level,
            "risk_score": float(risk_score),
            "recommendation": recommendation,
        },
        response_metadata=signals,
    )
    assessment, _ = RiskAssessment.objects.update_or_create(
        verification=verification,
        defaults={
            "tenant": verification.tenant,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "signals_json": signals,
            "recommendation": recommendation,
        },
    )
    return assessment


def apply_automatic_decision(
    verification, risk_assessment: RiskAssessment
) -> VerificationDecision:
    now = timezone.now()
    decision_map = {
        RiskRecommendation.APPROVE: VerificationStatus.VERIFIED,
        RiskRecommendation.REJECT: VerificationStatus.REJECTED,
        RiskRecommendation.MANUAL_REVIEW: VerificationStatus.MANUAL_REVIEW_REQUIRED,
    }
    decision = decision_map[risk_assessment.recommendation]
    reason_code_map = {
        RiskRecommendation.APPROVE: "risk_rules_approved",
        RiskRecommendation.REJECT: "risk_rules_rejected",
        RiskRecommendation.MANUAL_REVIEW: "risk_rules_manual_review",
    }
    detail_map = {
        RiskRecommendation.APPROVE: "Automatic approval based on currently available verification evidence.",
        RiskRecommendation.REJECT: "Automatic rejection based on failed or high-risk verification evidence.",
        RiskRecommendation.MANUAL_REVIEW: "Automatic review routing because the current evidence remains inconclusive.",
    }
    decision_record, _ = VerificationDecision.objects.update_or_create(
        verification=verification,
        defaults={
            "tenant": verification.tenant,
            "decision": decision,
            "decision_type": VerificationDecisionType.AUTOMATIC,
            "reason_code": reason_code_map[risk_assessment.recommendation],
            "reason_detail": detail_map[risk_assessment.recommendation],
            "evidence_summary_json": {
                "risk_assessment_id": risk_assessment.public_id,
                "risk_level": risk_assessment.risk_level,
                "risk_score": float(risk_assessment.risk_score),
                "recommendation": risk_assessment.recommendation,
                "signals": risk_assessment.signals_json,
            },
            "decided_by": None,
            "decided_at": now,
        },
    )
    verification.status = decision
    if decision in {
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.FAILED,
    }:
        verification.completed_at = now
        verification.save(update_fields=["status", "completed_at", "updated_at"])
    else:
        verification.save(update_fields=["status", "updated_at"])
    return decision_record


def run_verification_risk_and_decision(
    verification,
) -> tuple[RiskAssessment, VerificationDecision]:
    risk_assessment = evaluate_risk_assessment(verification)
    decision_record = apply_automatic_decision(verification, risk_assessment)
    return risk_assessment, decision_record
