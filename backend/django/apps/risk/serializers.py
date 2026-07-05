from apps.risk.models import RiskAssessment


def serialize_risk_assessment(risk_assessment: RiskAssessment) -> dict:
    return {
        "id": risk_assessment.public_id,
        "verification_id": risk_assessment.verification.public_id,
        "risk_score": float(risk_assessment.risk_score),
        "risk_level": risk_assessment.risk_level,
        "recommendation": risk_assessment.recommendation,
        "signals": risk_assessment.signals_json,
        "created_at": risk_assessment.created_at.isoformat(),
        "updated_at": risk_assessment.updated_at.isoformat(),
    }
