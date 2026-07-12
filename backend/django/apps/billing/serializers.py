from apps.billing.models import BillingRecord


def serialize_billing_record(record: BillingRecord) -> dict:
    return {
        "id": record.public_id,
        "organization_id": record.organization.public_id,
        "tenant_id": record.tenant.public_id,
        "title": record.title,
        "subtitle": record.subtitle,
        "status": record.status,
        "monthly_recurring_revenue": record.monthly_recurring_revenue,
        "monthly_check_count": record.monthly_check_count,
        "current_invoice": record.current_invoice,
        "plan": record.plan,
        "billing_cycle": record.billing_cycle,
        "owner_team": record.owner_team,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }
