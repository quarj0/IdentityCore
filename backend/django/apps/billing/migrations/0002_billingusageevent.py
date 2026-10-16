# Unrated usage facts; no pricing, payment collection, or automatic charges.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
        ("providers", "0011_alter_providerassignment_assignment_key_and_more"),
        ("projects", "0002_alter_project_deleted_at_alter_project_public_id"),
        ("tenants", "0006_tenantstorageroute"),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingUsageEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("public_id", models.CharField(editable=False, max_length=64, unique=True)),
                ("environment", models.CharField(choices=[("sandbox", "Sandbox"), ("production", "Production")], max_length=16)),
                ("capability", models.CharField(max_length=32)),
                ("provider_scope", models.CharField(choices=[("tenant_owned", "Tenant owned"), ("platform", "Platform owned")], max_length=16)),
                ("outcome", models.CharField(max_length=16)),
                ("quantity", models.PositiveSmallIntegerField(default=1)),
                ("rating_state", models.CharField(default="unrated", max_length=16)),
                ("occurred_at", models.DateTimeField()),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="billing_usage_events", to="projects.project")),
                ("provider_check", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="billing_usage_event", to="providers.providercheck")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="billing_usage_events", to="tenants.tenant")),
            ],
            options={
                "ordering": ["-occurred_at"],
                "indexes": [models.Index(fields=["tenant", "environment", "occurred_at"], name="bill_usage_ten_env_time")],
            },
        ),
    ]
