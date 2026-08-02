import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_normalize_invitation_fields")]

    operations = [
        migrations.CreateModel(
            name="RefreshTokenSession",
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
                ("jti", models.CharField(max_length=255, unique=True)),
                ("family_id", models.UUIDField(db_index=True, default=uuid.uuid4)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refresh_token_sessions",
                        to="accounts.platformuser",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="refreshtokensession",
            index=models.Index(
                fields=["family_id", "revoked_at"],
                name="accounts_re_family__673676_idx",
            ),
        ),
    ]
