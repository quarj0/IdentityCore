# Generated manually for tenant-scoped provider routing.

import common.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
        ("providers", "0003_alter_provider_configuration_json_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="provider",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="providers",
                to="tenants.tenant",
            ),
        ),
        migrations.CreateModel(
            name="ProviderAssignment",
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
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "public_id",
                    models.CharField(editable=False, max_length=64, unique=True),
                ),
                (
                    "assignment_key",
                    models.CharField(
                        choices=[
                            ("document_ocr", "Document OCR"),
                            ("document_classification", "Document Classification"),
                            ("document_quality", "Document Quality"),
                            ("face_match", "Face Match"),
                            ("liveness", "Liveness"),
                            ("identity_lookup", "Identity Lookup"),
                            ("risk_check", "Risk Check"),
                            ("notification_email", "Notification Email"),
                            ("notification_sms", "Notification SMS"),
                            ("notification_in_app", "Notification In-App"),
                        ],
                        db_index=True,
                        max_length=64,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("disabled", "Disabled"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=32,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignments",
                        to="providers.provider",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_assignments",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "ordering": ["tenant_id", "assignment_key", "created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="providerassignment",
            constraint=models.UniqueConstraint(
                fields=("tenant", "assignment_key"),
                name="provider_assignment_tenant_key_uniq",
            ),
        ),
    ]
