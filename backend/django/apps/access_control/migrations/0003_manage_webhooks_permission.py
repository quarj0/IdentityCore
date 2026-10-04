from django.db import migrations


def create_manage_webhooks_permission(apps, schema_editor):
    permission_model = apps.get_model("access_control", "Permission")
    role_model = apps.get_model("access_control", "Role")
    role_permission_model = apps.get_model("access_control", "RolePermission")
    permission, _ = permission_model.objects.update_or_create(
        code="manage_webhooks",
        defaults={
            "name": "Manage webhooks",
            "description": "Replay failed webhook deliveries and manage webhook delivery controls.",
        },
    )
    administrator_roles = role_model.objects.filter(
        is_system_role=True,
        scope="tenant",
        name__in=["Tenant Administrator", "Organization Administrator"],
    )
    role_permission_model.objects.bulk_create(
        [
            role_permission_model(role=role, permission=permission)
            for role in administrator_roles
        ],
        ignore_conflicts=True,
    )


def remove_manage_webhooks_permission(apps, schema_editor):
    permission_model = apps.get_model("access_control", "Permission")
    permission_model.objects.filter(code="manage_webhooks").delete()


class Migration(migrations.Migration):
    dependencies = [("access_control", "0002_initial")]

    operations = [
        migrations.RunPython(
            create_manage_webhooks_permission,
            remove_manage_webhooks_permission,
        )
    ]
