from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.biometrics.models import FaceMatchStatus, LivenessCheckStatus
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.providers.services import create_provider_check, get_or_create_system_provider
from apps.risk.models import RiskAssessment, RiskLevel, RiskRecommendation
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)
from apps.verifications.transitions import transition_verification, TERMINAL_STATUSES
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verifications.decision_contract import (
    DECISION_CONTRACT_VERSION,
    build_decision_input_snapshot,
)


def _get_policy_thresholds(verification) -> tuple[Decimal, Decimal]:
    snapshot = verification.policy_snapshot_json or {}
    face_match_threshold = Decimal(str(snapshot.get("face_match_threshold", "0.8500")))
    manual_review_threshold = Decimal(
        str(snapshot.get("manual_review_threshold", "0.6500"))
    )
    return face_match_threshold, manual_review_threshold


def _document_requires_manual_review(classification: dict | None) -> bool:
    if not isinstance(classification, dict):
        return False
    manual_review = classification.get("manual_review") or {}
    return bool(
        classification.get("provider_error")
        or "document_ocr_unavailable" in (classification.get("issues") or [])
        or "document_ocr_unavailable" in (manual_review.get("reason_codes") or [])
        or classification.get("requires_manual_review")
        or classification.get("workflow_action") == "continue_with_review"
        or manual_review.get("required")
    )


def _safe_authenticity_evidence(bundle):
    if not isinstance(bundle, dict):
        return None
    fields = {
        "authenticity_version",
        "status",
        "verdict",
        "confidence",
        "model_name",
        "model_version",
        "source_size",
        "coordinate_space",
        "regions",
    }
    return {
        "authenticity_version": bundle.get("authenticity_version"),
        "requires_manual_review": bundle.get("requires_manual_review", True),
        "captures": [
            {
                "capture_id": item.get("capture_id"),
                "provider_check_id": item.get("provider_check_id"),
                "result": {
                    key: value
                    for key, value in item.get("result", {}).items()
                    if key in fields
                },
            }
            for item in bundle.get("captures", [])[:20]
        ],
    }


def evaluate_risk_assessment(verification, *, external_evidence=None) -> RiskAssessment:
    latest_liveness_check = verification.liveness_checks.order_by("-checked_at").first()
    latest_face_match = verification.face_matches.order_by("-matched_at").first()
    latest_identity_document = verification.identity_documents.order_by(
        "-created_at"
    ).first()
    document_classification = (
        (latest_identity_document.extracted_data_json or {}).get(
            "document_classification"
        )
        if latest_identity_document is not None
        else None
    )
    face_match_threshold, manual_review_threshold = _get_policy_thresholds(verification)

    authenticity = (
        (latest_identity_document.extracted_data_json or {}).get(
            "document_authenticity"
        )
        if latest_identity_document
        else None
    )
    authenticity_review = bool(
        verification.policy_snapshot_json.get("document_authenticity_required")
        and (not authenticity or authenticity.get("requires_manual_review", True))
    )
    from apps.uploads.provenance import capture_signals
    from apps.identity_documents.consistency import collect_consistency
    from apps.risk.reuse import collect_reuse

    consistency = (
        collect_consistency(latest_identity_document, verification)
        if latest_identity_document
        else None
    )
    reuse = collect_reuse(verification)
    signals = {
        "duplicate_velocity": reuse,
        "capture_provenance": capture_signals(verification),
        "document_consistency": consistency,
        "document_authenticity": _safe_authenticity_evidence(authenticity),
        "document_submitted": verification.identity_documents.exists(),
        "document_classification": document_classification,
        "document_requires_manual_review": _document_requires_manual_review(
            document_classification
        )
        or authenticity_review,
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
    elif (
        _document_requires_manual_review(document_classification) or authenticity_review
    ):
        # Strong biometric evidence must not automatically approve a document
        # that was inconclusive, mismatched, or unavailable. Preserve the full
        # evidence set and route the completed case to a human reviewer.
        risk_score = Decimal("72.00")
        risk_level = RiskLevel.HIGH
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

    if consistency and consistency["recommended_action"] == "reject":
        risk_score, risk_level, recommendation = (
            Decimal("95.00"),
            RiskLevel.CRITICAL,
            RiskRecommendation.REJECT,
        )
    elif (
        consistency
        and consistency["recommended_action"] == "manual_review"
        and recommendation != RiskRecommendation.REJECT
    ):
        risk_score, risk_level, recommendation = (
            max(risk_score, Decimal("75.00")),
            RiskLevel.HIGH,
            RiskRecommendation.MANUAL_REVIEW,
        )

    if (
        reuse["recommended_action"] == "manual_review"
        and recommendation != RiskRecommendation.REJECT
    ):
        risk_score = max(risk_score, Decimal("75.00"))
        risk_level = RiskLevel.HIGH
        recommendation = RiskRecommendation.MANUAL_REVIEW
    if (
        signals["capture_provenance"]["invalid"]
        or signals["capture_provenance"]["truncated"]
    ) and recommendation != RiskRecommendation.REJECT:
        risk_score = max(risk_score, Decimal("82.00"))
        risk_level = RiskLevel.HIGH
        recommendation = RiskRecommendation.MANUAL_REVIEW

    from apps.risk.external import (
        apply_external_risk,
        minimal_inputs,
        risk_input_digest,
    )

    external = external_evidence
    if verification.policy_snapshot_json.get("external_risk_enabled") is True and (
        external is None
        or external.get("input_digest")
        != risk_input_digest(verification, minimal_inputs(signals))
    ):
        external = {
            "status": "unavailable",
            "risk_score": None,
            "signals": [],
            "risk_version": "1",
        }
    if external is not None:
        signals["external_risk"] = external
        risk_score, risk_level, recommendation = apply_external_risk(
            verification.policy_snapshot_json or {},
            external,
            score=risk_score,
            level=risk_level,
            recommendation=recommendation,
        )

    create_provider_check(
        provider_override=get_or_create_system_provider(ProviderCheckType.RISK_CHECK),
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


def _automatic_conflict(requested, current):
    existing = VerificationDecision.objects.filter(verification=current).first()
    reason = ""
    if current.status in TERMINAL_STATUSES or (
        existing and existing.decision in TERMINAL_STATUSES
    ):
        reason = "terminal_decision"
    elif existing and existing.decision_type == VerificationDecisionType.MANUAL:
        reason = "human_decision"
    elif requested.decision_revision != current.decision_revision:
        reason = "stale_revision"
    if reason:
        record_audit_event(
            tenant=current.tenant,
            action="verification.automatic_decision_conflict",
            target_type="verification",
            target_id=current.public_id,
            metadata={
                "reason": reason,
                "expected_revision": requested.decision_revision,
                "current_revision": current.decision_revision,
            },
        )
        for field in ("status", "completed_at", "updated_at", "decision_revision"):
            setattr(requested, field, getattr(current, field))
        if existing:
            existing._automatic_conflict = True
        return True, existing
    return False, None


@transaction.atomic
def apply_automatic_decision(
    verification, risk_assessment: RiskAssessment
) -> VerificationDecision | None:
    requested_verification = verification
    lock_audit_chain(verification.tenant_id)
    verification = (
        Verification.objects.select_for_update(of=("self",), no_key=True)
        .select_related("tenant", "verification_subject")
        .get(pk=verification.pk)
    )
    conflict, existing = _automatic_conflict(requested_verification, verification)
    if conflict:
        return existing
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
            "contract_version": DECISION_CONTRACT_VERSION,
            "reason_codes_json": [reason_code_map[risk_assessment.recommendation]],
            "input_snapshot_json": build_decision_input_snapshot(
                verification, risk_assessment=risk_assessment
            ),
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
    verification.decision_revision += 1
    verification.save(update_fields=["decision_revision", "updated_at"])
    transitioned, _ = transition_verification(verification, decision, completed_at=now)
    requested_verification.decision_revision = transitioned.decision_revision
    requested_verification.status = transitioned.status
    requested_verification.completed_at = transitioned.completed_at
    requested_verification.updated_at = transitioned.updated_at
    return decision_record


_UNPREPARED = object()


def run_verification_risk_and_decision(verification, *, external_evidence=_UNPREPARED):
    from apps.risk.external import prepare_external_risk

    if external_evidence is _UNPREPARED:
        external_evidence = prepare_external_risk(verification)
    return _commit_risk_and_decision(verification, external_evidence=external_evidence)


@transaction.atomic
def _commit_risk_and_decision(
    verification, *, external_evidence
) -> tuple[RiskAssessment | None, VerificationDecision | None]:
    lock_audit_chain(verification.tenant_id)
    current = (
        Verification.objects.select_for_update(of=("self",), no_key=True)
        .select_related("tenant", "verification_subject")
        .get(pk=verification.pk)
    )
    conflict, existing = _automatic_conflict(verification, current)
    if conflict:
        return RiskAssessment.objects.filter(verification=current).first(), existing
    # Hold the parent lock through evaluation and decision persistence. Human
    # finalizers use the same lock; stale worker revisions cannot become writes.
    risk_assessment = evaluate_risk_assessment(
        current, external_evidence=external_evidence
    )
    decision_record = apply_automatic_decision(verification, risk_assessment)
    return risk_assessment, decision_record
