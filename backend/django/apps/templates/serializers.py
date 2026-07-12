from apps.templates.models import Template


def serialize_template(template: Template) -> dict:
    return {
        "id": template.public_id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "status": template.status,
        "version": template.version,
        "countries": template.countries_json,
        "required_checks": template.required_checks_json,
        "usage_count": template.usage_count,
        "cloned_by_organizations": template.cloned_by_organizations,
        "owner_team": template.owner_team,
        "risk_level": template.risk_level,
        "created_by_id": template.created_by.public_id,
        "created_by_email": template.created_by.email,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }
