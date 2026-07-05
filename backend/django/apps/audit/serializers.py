from apps.audit.models import AuditEvent


def serialize_audit_event(event: AuditEvent) -> dict:
    return {
        "id": event.public_id,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "action": event.action,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "metadata": event.metadata_json,
        "created_at": event.created_at.isoformat(),
    }
