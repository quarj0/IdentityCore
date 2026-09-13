from django.db import migrations


def create_manage_webhooks_permission(apps, schema_editor):
    permission = apps.get_model("access_control", "Permission")
    permission.objects.update_or_create(
        code="manage_webhooks",
        defaults={
            "name": "Manage webhooks",
            "description": "Replay failed webhook deliveries and manage webhook delivery controls.",
        },
    )


def remove_manage_webhooks_permission(apps, schema_editor):
    permission = apps.get_model("access_control", "Permission")
    permission.objects.filter(code="manage_webhooks").delete()


class Migration(migrations.Migration):
    dependencies = [("access_control", "0002_initial")]

    operations = [
        migrations.RunPython(
            create_manage_webhooks_permission,
            remove_manage_webhooks_permission,
        )
    ]
