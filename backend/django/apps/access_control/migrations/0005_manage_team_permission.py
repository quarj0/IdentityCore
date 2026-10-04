from django.db import migrations


def grant(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    Role = apps.get_model("access_control", "Role")
    RolePermission = apps.get_model("access_control", "RolePermission")
    permission, _ = Permission.objects.get_or_create(
        code="manage_team", defaults={"name": "Manage team invitations"}
    )
    for role in Role.objects.filter(
        scope="tenant", name="Tenant Administrator", status="active"
    ):
        RolePermission.objects.get_or_create(role=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [("access_control", "0004_provider_configuration_permissions")]
    operations = [migrations.RunPython(grant, migrations.RunPython.noop)]
