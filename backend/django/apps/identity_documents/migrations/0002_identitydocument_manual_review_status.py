from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity_documents", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="identitydocument",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("processing", "Processing"),
                    ("processed", "Processed"),
                    ("manual_review_required", "Manual Review Required"),
                    ("failed", "Failed"),
                    ("rejected", "Rejected"),
                ],
                db_index=True,
                default="submitted",
                max_length=32,
            ),
        ),
    ]
