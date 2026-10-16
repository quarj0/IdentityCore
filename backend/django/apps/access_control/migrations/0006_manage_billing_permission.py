from django.db import migrations


def grant(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    Role = apps.get_model("access_control", "Role")
    RolePermission = apps.get_model("access_control", "RolePermission")
    permission, _ = Permission.objects.get_or_create(
        code="manage_billing", defaults={"name": "Manage organization billing"}
    )
    for role in Role.objects.filter(
        scope="tenant", is_system_role=True,
        name__in=("Tenant Administrator", "Organization Administrator"),
    ):
        RolePermission.objects.get_or_create(role=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [("access_control", "0005_manage_team_permission")]
    operations = [migrations.RunPython(grant, migrations.RunPython.noop)]
