from apps.access_control.models import Permission, Role


def serialize_role(role: Role) -> dict:
    return {
        "id": role.public_id,
        "name": role.name,
        "description": role.description,
        "scope": role.scope,
        "status": role.status,
        "is_system_role": role.is_system_role,
        "permission_codes": [
            role_permission.permission.code
            for role_permission in role.role_permissions.select_related(
                "permission"
            ).all()
        ],
    }


def serialize_permission(permission: Permission) -> dict:
    return {
        "code": permission.code,
        "name": permission.name,
        "description": permission.description,
    }
