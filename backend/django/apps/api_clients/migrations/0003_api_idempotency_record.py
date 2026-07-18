# Generated for persisted API-client idempotency.

import django.db.models.deletion
import common.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api_clients", "0002_api_client_project")]

    operations = [
        migrations.CreateModel(
            name="APIIdempotencyRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("key", models.CharField(max_length=255)),
                ("request_hash", models.CharField(max_length=64)),
                ("method", models.CharField(max_length=16)),
                ("path", models.CharField(max_length=512)),
                ("response_data_json", common.fields.EncryptedJSONField(blank=True, encryption_purpose="api_clients.idempotency.response", null=True)),
                ("response_status", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("api_client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="idempotency_records", to="api_clients.apiclient")),
            ],
            options={
                "indexes": [models.Index(fields=["api_client", "created_at"], name="api_clients_api_cli_8b5b2e_idx")],
                "constraints": [models.UniqueConstraint(fields=("api_client", "key"), name="unique_api_client_idempotency_key")],
            },
        ),
    ]
