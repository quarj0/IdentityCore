from apps.incidents.models import Incident


def serialize_incident(incident: Incident) -> dict:
    return {
        "id": incident.public_id,
        "title": incident.title,
        "summary": incident.summary,
        "status": incident.status,
        "severity": incident.severity,
        "owner_team": incident.owner_team,
        "affected_surface": incident.affected_surface,
        "detected_at": incident.detected_at.isoformat(),
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "metadata": incident.metadata_json,
        "created_at": incident.created_at.isoformat(),
        "updated_at": incident.updated_at.isoformat(),
    }
