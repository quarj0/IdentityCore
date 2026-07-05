from apps.organizations.models import Organization


def serialize_organization(organization: Organization) -> dict:
    return {
        "id": organization.public_id,
        "name": organization.name,
        "slug": organization.slug,
        "industry": organization.industry,
        "status": organization.status,
        "default_country_profile_id": organization.default_country_profile_id,
        "default_jurisdiction_id": organization.default_jurisdiction_id,
        "settings": organization.settings_json,
        "created_at": organization.created_at.isoformat(),
        "updated_at": organization.updated_at.isoformat(),
    }
