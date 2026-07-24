from django.db import migrations, models


def backfill_review_owners(apps, schema_editor):
    Verification = apps.get_model("verifications", "Verification")
    for verification in Verification.objects.all().iterator():
        metadata = verification.metadata_json or {}
        if metadata.get("workflow") == "administrator_onboarding":
            verification.review_owner = "platform"
            verification.save(update_fields=["review_owner"])


class Migration(migrations.Migration):
    dependencies = [("verifications", "0004_verificationmobilehandoff")]

    operations = [
        migrations.AddField(
            model_name="verification",
            name="review_owner",
            field=models.CharField(
                choices=[("tenant", "Tenant"), ("platform", "Platform")],
                db_index=True,
                default="tenant",
                max_length=16,
            ),
        ),
        migrations.RunPython(backfill_review_owners, migrations.RunPython.noop),
    ]
