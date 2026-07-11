import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("accounts", "0003_passwordresettoken_contactinquiry"),
        ("projects", "0001_initial"),
        ("verification_policies", "0002_policy_project"),
    ]
    operations = [
        migrations.CreateModel(
            name="Workflow",
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
                ("description", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("published", "Published"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("steps_json", models.JSONField(default=list)),
                ("settings_json", models.JSONField(default=dict)),
                ("current_version", models.PositiveIntegerField(default=0)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_workflows",
                        to="accounts.platformuser",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workflows",
                        to="projects.project",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workflows",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="workflow",
            constraint=models.UniqueConstraint(
                fields=("project", "name"), name="workflow_project_name_uniq"
            ),
        ),
        migrations.CreateModel(
            name="WorkflowVersion",
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
                (
                    "public_id",
                    models.CharField(
                        db_index=True, editable=False, max_length=64, unique=True
                    ),
                ),
                ("version", models.PositiveIntegerField()),
                ("steps_json", models.JSONField(default=list)),
                ("settings_json", models.JSONField(default=dict)),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                (
                    "policy",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workflow_version",
                        to="verification_policies.verificationpolicy",
                    ),
                ),
                (
                    "published_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_workflow_versions",
                        to="accounts.platformuser",
                    ),
                ),
                (
                    "workflow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="versions",
                        to="workflows.workflow",
                    ),
                ),
            ],
            options={"ordering": ["-version"]},
        ),
        migrations.AddConstraint(
            model_name="workflowversion",
            constraint=models.UniqueConstraint(
                fields=("workflow", "version"), name="workflow_version_uniq"
            ),
        ),
    ]
