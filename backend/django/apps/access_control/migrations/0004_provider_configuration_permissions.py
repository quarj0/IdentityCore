from django.db import migrations


def seed(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    Role = apps.get_model("access_control", "Role")
    RolePermission = apps.get_model("access_control", "RolePermission")
    roles = Role.objects.filter(
        is_system_role=True,
        scope="tenant",
        name__in=["Tenant Administrator", "Organization Administrator"],
    )
    for code, name in (
        ("manage_providers", "Manage providers"),
        ("approve_provider_promotion", "Approve provider promotion"),
    ):
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"name": name}
        )
        RolePermission.objects.bulk_create(
            [RolePermission(role=role, permission=permission) for role in roles],
            ignore_conflicts=True,
        )


class Migration(migrations.Migration):
    dependencies = [("access_control", "0003_manage_webhooks_permission")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
