from apps.audit.models import AuditEvent

ACTION_LABELS = {
    "user.login": "Signed in",
    "graphql.query": "Viewed platform data",
    "graphql.mutation": "Updated platform data",
    "project.created": "Created a project",
    "workflow.created": "Created a workflow",
    "onboarding.started": "Started onboarding",
    "onboarding.email_verified": "Verified onboarding email",
    "onboarding.organization_verification_submitted": "Submitted organization verification",
    "onboarding.administrator_verification_started": "Started administrator verification",
    "onboarding.administrator_verification_resumed": "Resumed administrator verification",
    "onboarding.administrator_identity_submitted": "Submitted administrator verification",
    "onboarding.review_approved": "Approved organization review",
    "onboarding.review_rejected": "Rejected organization review",
    "onboarding.review_needs_information": "Requested more information",
    "organization.supporting_document.deleted": "Deleted supporting document",
    "workspace.suspended": "Suspended workspace",
}

TARGET_LABELS = {
    "graphql": "Platform request",
    "organization": "Organization",
    "organization_supporting_document": "Supporting document",
    "platform_user": "Platform user",
    "tenant": "Workspace",
    "verification": "Verification",
}


def _humanize(value: str) -> str:
    return value.replace(".", " ").replace("_", " ").title()


def serialize_audit_event(event: AuditEvent) -> dict:
    actor_display_name = "System"
    if event.actor_type == "platform_user" and event.actor_id:
        user = event.tenant.platform_users.filter(public_id=event.actor_id).first()
        if user:
            actor_display_name = f"{user.first_name} {user.last_name}".strip() or user.email
            if user.email and user.email not in actor_display_name:
                actor_display_name = f"{actor_display_name} ({user.email})"
    elif event.actor_id:
        actor_display_name = _humanize(event.actor_type)
    action_label = ACTION_LABELS.get(event.action, _humanize(event.action))
    target_label = TARGET_LABELS.get(event.target_type, _humanize(event.target_type))
    return {
        "id": event.public_id,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "action": event.action,
        "action_label": action_label,
        "actor_display_name": actor_display_name,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "target_label": target_label,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "metadata": event.metadata_json,
        "created_at": event.created_at.isoformat(),
    }
