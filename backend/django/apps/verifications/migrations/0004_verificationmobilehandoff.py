import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("verifications", "0003_alter_verification_metadata_json_and_more")]

    operations = [
        migrations.CreateModel(
            name="VerificationMobileHandoff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.CharField(db_index=True, editable=False, max_length=64, unique=True)),
                ("token_hash", models.CharField(max_length=255)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("redeemed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("redeemed_session", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="redeemed_mobile_handoff", to="verifications.verificationsession")),
                ("source_session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mobile_handoffs", to="verifications.verificationsession")),
            ],
        ),
    ]
