from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("workflows", "0001_initial")]
    operations = [
        migrations.AlterField(
            model_name="workflow",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="workflow",
            name="public_id",
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name="workflowversion",
            name="public_id",
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
    ]
