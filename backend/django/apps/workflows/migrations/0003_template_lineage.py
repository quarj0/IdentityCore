import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("templates", "0002_workflow_definition"),
        ("workflows", "0002_normalize_inherited_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="workflow",
            name="source_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="instantiated_workflows",
                to="templates.template",
            ),
        ),
        migrations.AddField(
            model_name="workflow",
            name="source_template_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="workflow",
            name="instantiation_key",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddConstraint(
            model_name="workflow",
            constraint=models.UniqueConstraint(
                condition=~models.Q(instantiation_key=""),
                fields=("tenant", "instantiation_key"),
                name="workflow_tenant_instantiation_key_uniq",
            ),
        ),
    ]
