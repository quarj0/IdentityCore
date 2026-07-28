from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("templates", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="template",
            name="slug",
            field=models.SlugField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name="template",
            name="steps_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="template",
            name="settings_json",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="template",
            name="provider_requirements_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="template",
            name="output_claims_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddConstraint(
            model_name="template",
            constraint=models.UniqueConstraint(
                condition=~models.Q(slug=""),
                fields=("slug", "version"),
                name="template_slug_version_uniq",
            ),
        ),
    ]
