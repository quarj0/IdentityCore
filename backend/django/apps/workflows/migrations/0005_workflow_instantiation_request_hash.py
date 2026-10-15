from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("workflows", "0004_workflowversion_workflow_name")]

    operations = [
        migrations.AddField(
            model_name="workflow",
            name="instantiation_request_hash",
            field=models.CharField(max_length=64, blank=True, editable=False),
        ),
    ]
