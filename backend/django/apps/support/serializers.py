from apps.support.models import SupportTicket


def serialize_support_ticket(ticket: SupportTicket) -> dict:
    return {
        "id": ticket.public_id,
        "organization_id": ticket.organization.public_id if ticket.organization else None,
        "organization_name": ticket.organization.name if ticket.organization else "",
        "title": ticket.title,
        "summary": ticket.summary,
        "status": ticket.status,
        "priority": ticket.priority,
        "owner_team": ticket.owner_team,
        "issue_type": ticket.issue_type,
        "requester_email": ticket.requester_email,
        "metadata": ticket.metadata_json,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }
