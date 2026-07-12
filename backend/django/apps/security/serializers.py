from apps.security.models import SecurityCase


def serialize_security_case(case: SecurityCase) -> dict:
    return {
        "id": case.public_id,
        "title": case.title,
        "summary": case.summary,
        "status": case.status,
        "severity": case.severity,
        "owner_team": case.owner_team,
        "signal": case.signal,
        "affected_surface": case.affected_surface,
        "detected_at": case.detected_at.isoformat(),
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "metadata": case.metadata_json,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }
