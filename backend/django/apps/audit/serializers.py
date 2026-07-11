from apps.audit.models import AuditEvent

ACTION_LABELS = {
    "user.login": "Signed in",
    "project.created": "Created a project",
    "workflow.created": "Created a workflow",
    "onboarding.organization_verification_submitted": "Submitted organization verification",
    "onboarding.administrator_identity_submitted": "Submitted administrator verification",
}


def serialize_audit_event(event: AuditEvent) -> dict:
    actor_display_name = "System"
    if event.actor_type == "platform_user" and event.actor_id:
        user = event.tenant.platform_users.filter(public_id=event.actor_id).first()
        if user:
            actor_display_name = f"{user.first_name} {user.last_name}".strip() or user.email
            if user.email and user.email not in actor_display_name:
                actor_display_name = f"{actor_display_name} ({user.email})"
    elif event.actor_id:
        actor_display_name = event.actor_type.replace("_", " ").title()
    return {
        "id": event.public_id,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "action": event.action,
        "action_label": ACTION_LABELS.get(event.action, event.action.replace(".", " ").replace("_", " ").title()),
        "actor_display_name": actor_display_name,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "target_label": event.target_type.replace("_", " ").title(),
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "metadata": event.metadata_json,
        "created_at": event.created_at.isoformat(),
    }
