from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("consent", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="consentrecord",
            name="consent_locale",
            field=models.CharField(default="en", max_length=16),
        ),
        migrations.AddField(
            model_name="consentrecord",
            name="consent_content_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
