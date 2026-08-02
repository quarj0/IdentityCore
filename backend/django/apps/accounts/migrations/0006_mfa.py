from django.db import migrations, models
import django.db.models.deletion
import common.fields


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_normalize_invitation_fields")]
    operations = [
        migrations.AddField(
            model_name="platformuser",
            name="mfa_config_json",
            field=common.fields.EncryptedJSONField(
                blank=True, default=dict, encryption_purpose="accounts.mfa_config"
            ),
        ),
        migrations.CreateModel(
            name="MFARecoveryCode",
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
                ("code_hash", models.CharField(max_length=64)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mfa_recovery_codes",
                        to="accounts.platformuser",
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="mfarecoverycode",
            constraint=models.UniqueConstraint(
                fields=("user", "code_hash"), name="accounts_mfa_recovery_code_unique"
            ),
        ),
    ]
