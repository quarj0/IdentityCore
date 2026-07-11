import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("accounts", "0003_passwordresettoken_contactinquiry"),
        ("tenants", "0003_alter_tenant_settings_json"),
    ]
    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "public_id",
                    models.CharField(
                        db_index=True, editable=False, max_length=64, unique=True
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255)),
                (
                    "environment",
                    models.CharField(
                        choices=[("sandbox", "Sandbox"), ("production", "Production")],
                        default="sandbox",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=16,
                    ),
                ),
                ("allowed_origins_json", models.JSONField(blank=True, default=list)),
                ("is_default", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_projects",
                        to="accounts.platformuser",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="projects",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={"ordering": ["environment", "name"]},
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                fields=("tenant", "slug"), name="project_tenant_slug_uniq"
            ),
        ),
    ]
