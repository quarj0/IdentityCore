from django.db import migrations


def repair_incomplete_decision_contracts(apps, schema_editor):
    decision_model = apps.get_model("verifications", "VerificationDecision")
    queryset = decision_model.objects
    if schema_editor is not None:
        queryset = queryset.using(schema_editor.connection.alias)
    for decision in queryset.filter(
        contract_version="1",
        verification__deleted_at__isnull=True,
        verification__verification_subject__deleted_at__isnull=True,
    ).iterator():
        if decision.input_snapshot_json and decision.reason_codes_json:
            continue
        decision.contract_version = "legacy"
        decision.save(update_fields=["contract_version"])


class Migration(migrations.Migration):
    dependencies = [("verifications", "0023_processingjob_lease_generation")]
    operations = [
        migrations.RunPython(
            repair_incomplete_decision_contracts, migrations.RunPython.noop
        )
    ]
