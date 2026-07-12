from apps.providers.models import Provider, ProviderAssignment, ProviderCheck


def serialize_provider(provider: Provider) -> dict:
    return {
        "id": provider.public_id,
        "tenant_id": provider.tenant.public_id if provider.tenant else None,
        "tenant_name": provider.tenant.name if provider.tenant else None,
        "name": provider.name,
        "code": provider.code,
        "provider_type": provider.provider_type,
        "status": provider.status,
        "configuration": provider.configuration_json,
        "created_at": provider.created_at.isoformat(),
        "updated_at": provider.updated_at.isoformat(),
    }


def serialize_provider_check(provider_check: ProviderCheck) -> dict:
    return {
        "id": provider_check.public_id,
        "verification_id": provider_check.verification.public_id,
        "provider_id": provider_check.provider.public_id,
        "provider_code": provider_check.provider.code,
        "check_type": provider_check.check_type,
        "status": provider_check.status,
        "provider_reference": provider_check.provider_reference,
        "request_metadata": provider_check.request_metadata_json,
        "response_metadata": provider_check.response_metadata_json,
        "normalized_result": provider_check.normalized_result_json,
        "error_code": provider_check.error_code,
        "error_message": provider_check.error_message,
        "started_at": provider_check.started_at.isoformat(),
        "completed_at": (
            provider_check.completed_at.isoformat()
            if provider_check.completed_at
            else None
        ),
    }


def serialize_provider_assignment(provider_assignment: ProviderAssignment) -> dict:
    return {
        "id": provider_assignment.public_id,
        "tenant_id": provider_assignment.tenant.public_id,
        "tenant_name": provider_assignment.tenant.name,
        "assignment_key": provider_assignment.assignment_key,
        "provider_id": provider_assignment.provider.public_id,
        "provider_name": provider_assignment.provider.name,
        "provider_code": provider_assignment.provider.code,
        "provider_type": provider_assignment.provider.provider_type,
        "status": provider_assignment.status,
        "notes": provider_assignment.notes,
        "created_at": provider_assignment.created_at.isoformat(),
        "updated_at": provider_assignment.updated_at.isoformat(),
    }
