from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("providers", "0004_provider_tenant_and_assignment")]

    operations = [
        migrations.AddField(
            model_name="providercheck",
            name="duration_ms",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
