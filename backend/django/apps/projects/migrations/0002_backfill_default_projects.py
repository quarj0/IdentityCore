from django.db import migrations


def forwards(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    Project = apps.get_model("projects", "Project")
    User = apps.get_model("accounts", "PlatformUser")
    for tenant in Tenant.objects.all():
        user = User.objects.filter(tenant=tenant).order_by("created_at").first()
        if not user:
            continue
        project, _ = Project.objects.get_or_create(
            tenant=tenant,
            slug="default-sandbox",
            defaults={
                "name": "Default Sandbox",
                "environment": "sandbox",
                "status": "active",
                "is_default": True,
                "created_by": user,
            },
        )
        for app, model in (
            ("api_clients", "APIClient"),
            ("webhooks", "WebhookEndpoint"),
            ("verification_policies", "VerificationPolicy"),
            ("verifications", "Verification"),
        ):
            apps.get_model(app, model).objects.filter(
                tenant=tenant, project__isnull=True
            ).update(project=project)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
        ("api_clients", "0002_api_client_project"),
        ("webhooks", "0003_webhook_endpoint_project"),
        ("verification_policies", "0002_policy_project"),
        ("verifications", "0005_verification_project"),
    ]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
