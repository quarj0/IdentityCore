from django.db import migrations, models


def backfill_workflow_names(apps, schema_editor):
    WorkflowVersion = apps.get_model("workflows", "WorkflowVersion")
    for version in WorkflowVersion.objects.select_related("workflow").iterator():
        version.workflow_name = version.workflow.name
        version.save(update_fields=["workflow_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("workflows", "0003_template_lineage"),
    ]

    operations = [
        migrations.AddField(
            model_name="workflowversion",
            name="workflow_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_workflow_names, migrations.RunPython.noop),
    ]
