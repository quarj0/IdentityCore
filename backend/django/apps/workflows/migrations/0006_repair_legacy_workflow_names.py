from django.db import migrations
from django.db.migrations.recorder import MigrationRecorder
from ._legacy_names import recovered_name


def repair(apps, schema_editor):
    alias = schema_editor.connection.alias
    applied = (
        MigrationRecorder.Migration.objects.using(alias)
        .filter(app="workflows", name="0004_workflowversion_workflow_name")
        .values_list("applied", flat=True)
        .first()
    )
    if applied is None:
        return
    Version = apps.get_model("workflows", "WorkflowVersion")
    for version in (
        Version.objects.using(alias)
        .filter(published_at__lte=applied)
        .select_related("workflow", "policy", "published_by")
        .iterator()
    ):
        name = recovered_name(version)
        if version.workflow_name != name:
            version.workflow_name = name
            version.save(using=alias, update_fields=["workflow_name"])


class Migration(migrations.Migration):
    dependencies = [("workflows", "0005_workflow_instantiation_request_hash")]
    operations = [migrations.RunPython(repair, migrations.RunPython.noop)]
