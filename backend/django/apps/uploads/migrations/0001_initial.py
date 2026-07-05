from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenants", "0001_initial"),
        ("verifications", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Upload",
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
                    "purpose",
                    models.CharField(
                        choices=[
                            ("document_capture", "Document Capture"),
                            ("selfie_capture", "Selfie Capture"),
                            ("liveness_capture", "Liveness Capture"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("storage_key", models.CharField(max_length=255, unique=True)),
                ("storage_provider", models.CharField(default="local", max_length=64)),
                ("mime_type", models.CharField(max_length=100)),
                ("file_size_bytes", models.PositiveBigIntegerField()),
                ("checksum_sha256", models.CharField(blank=True, max_length=64)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("initiated", "Initiated"),
                            ("consumed", "Consumed"),
                            ("expired", "Expired"),
                            ("deleted", "Deleted"),
                        ],
                        db_index=True,
                        default="initiated",
                        max_length=32,
                    ),
                ),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="uploads",
                        to="tenants.tenant",
                    ),
                ),
                (
                    "verification",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="uploads",
                        to="verifications.verification",
                    ),
                ),
                (
                    "verification_session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="uploads",
                        to="verifications.verificationsession",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
