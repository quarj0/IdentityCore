from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("uploads", "0004_upload_quarantine_reason_alter_upload_status")]

    operations = [
        migrations.AddField(
            model_name="upload",
            name="deletion_attempt_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="upload",
            name="deletion_retry_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
