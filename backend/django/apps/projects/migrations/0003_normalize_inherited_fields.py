from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0002_backfill_default_projects")]
    operations = [
        migrations.AlterField(
            model_name="project",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="public_id",
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
    ]
