from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("verifications", "0022_reviewqueue_sampling_percent_reviewqualityassignment")]
    operations = [migrations.AddField(
        model_name="processingjob", name="lease_generation",
        field=models.PositiveIntegerField(default=0, db_default=0),
    )]
