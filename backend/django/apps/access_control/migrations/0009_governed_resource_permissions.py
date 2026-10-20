from django.db import migrations


PERMISSIONS = {
    "read_evidence": "Read purpose-scoped evidence",
    "manage_evidence": "Manage governed evidence and schemas",
    "read_claims": "Read purpose-scoped claims",
    "manage_claims": "Manage reusable claims",
    "disclose_claims": "Disclose purpose-scoped claims",
    "manage_provider_assurance": "Manage provider assurance evidence",
    "approve_provider_assurance": "Independently approve provider assurance",
}


def grant(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    Role = apps.get_model("access_control", "Role")
    RolePermission = apps.get_model("access_control", "RolePermission")
    for code, name in PERMISSIONS.items():
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"name": name}
        )
        for role in Role.objects.filter(
            scope="tenant",
            is_system_role=True,
            name__in=["Tenant Administrator", "Organization Administrator"],
        ):
            RolePermission.objects.get_or_create(role=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [("access_control", "0008_manage_subject_privacy_permission")]
    operations = [migrations.RunPython(grant, migrations.RunPython.noop)]
