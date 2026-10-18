from django.db import migrations


def grant(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")
    Role = apps.get_model("access_control", "Role")
    RolePermission = apps.get_model("access_control", "RolePermission")
    permission, _ = Permission.objects.get_or_create(
        code="review_verification", defaults={"name": "Review verification cases"}
    )
    for role in Role.objects.filter(
        scope="tenant",
        is_system_role=True,
        name__in=[
            "Tenant Administrator",
            "Organization Administrator",
            "Verification Officer",
        ],
    ):
        RolePermission.objects.get_or_create(role=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [("access_control", "0006_manage_billing_permission")]
    operations = [migrations.RunPython(grant, migrations.RunPython.noop)]
