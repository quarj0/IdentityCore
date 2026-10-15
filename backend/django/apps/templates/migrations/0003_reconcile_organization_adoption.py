from django.db import migrations


def reconcile_organization_adoption(apps, schema_editor):
    Template = apps.get_model("templates", "Template")
    Workflow = apps.get_model("workflows", "Workflow")
    alias = schema_editor.connection.alias
    for template in Template.objects.using(alias).select_for_update().iterator():
        organizations = (
            Workflow.objects.using(alias)
            .filter(source_template_id=template.pk)
            .order_by()
            .values("tenant__organization_id")
            .distinct()
            .count()
        )
        Template.objects.using(alias).filter(pk=template.pk).update(
            cloned_by_organizations=organizations
        )


class Migration(migrations.Migration):
    dependencies = [
        ("templates", "0002_workflow_definition"),
        ("workflows", "0005_workflow_instantiation_request_hash"),
    ]

    operations = [
        migrations.RunPython(
            reconcile_organization_adoption, migrations.RunPython.noop
        ),
    ]
