from django.db import migrations


def mark_incomplete_decision_contracts_legacy(apps, schema_editor):
    VerificationDecision = apps.get_model("verifications", "VerificationDecision")
    for decision in VerificationDecision.objects.filter(contract_version="1").iterator():
        if decision.input_snapshot_json or decision.reason_codes_json:
            continue
        decision.contract_version = "legacy"
        decision.save(update_fields=["contract_version"])


class Migration(migrations.Migration):
    dependencies = [
        ("verifications", "0017_backfill_workflow_snapshots"),
    ]

    operations = [
        migrations.RunPython(
            mark_incomplete_decision_contracts_legacy,
            migrations.RunPython.noop,
        ),
    ]
