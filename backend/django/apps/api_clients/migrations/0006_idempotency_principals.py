from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_idempotency_scope(apps, schema_editor):
    record_model = apps.get_model("api_clients", "APIIdempotencyRecord")
    for record in record_model.objects.select_related("api_client").iterator():
        record.tenant_id = record.api_client.tenant_id
        record.operation = "verification.create"
        record.save(update_fields=["tenant_id", "operation"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api_clients", "0005_apiclient_previous_client_secret_expires_at_and_more"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="apiidempotencyrecord",
            name="operation",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="apiidempotencyrecord",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="idempotency_records",
                to="tenants.tenant",
            ),
        ),
        migrations.AddField(
            model_name="apiidempotencyrecord",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="idempotency_records",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="apiidempotencyrecord",
            name="api_client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="idempotency_records",
                to="api_clients.apiclient",
            ),
        ),
        migrations.RunPython(populate_idempotency_scope, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="apiidempotencyrecord",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="idempotency_records",
                to="tenants.tenant",
            ),
        ),
    ]
