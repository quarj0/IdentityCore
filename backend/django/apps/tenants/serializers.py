from apps.tenants.models import Tenant


def serialize_tenant(tenant: Tenant) -> dict:
    return {
        "id": tenant.public_id,
        "organization_id": tenant.organization.public_id,
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status,
        "settings": tenant.settings_json,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat(),
    }
