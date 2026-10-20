from django.db import migrations
from django.db.migrations.recorder import MigrationRecorder


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
    Verification = apps.get_model("verifications", "Verification")
    for version in (
        Version.objects.using(alias)
        .filter(published_at__lte=applied)
        .select_related("workflow", "policy")
        .iterator()
    ):
        for case in (
            Verification.objects.using(alias)
            .filter(
                tenant_id=version.workflow.tenant_id,
                policy_public_id=version.policy.public_id,
            )
            .iterator()
        ):
            snapshot = case.workflow_snapshot_json
            if (
                not isinstance(snapshot, dict)
                or snapshot.get("id") != version.public_id
                or snapshot.get("workflow_name") == version.workflow_name
            ):
                continue
            snapshot = dict(snapshot)
            previous = snapshot.get("workflow_name")
            snapshot["workflow_name"] = version.workflow_name
            snapshot["workflow_name_backfill_correction"] = {
                "previous_assertion": previous,
                "source": (
                    "published_policy" if version.workflow_name else "unavailable"
                ),
                "reason": "legacy_backfill_used_mutable_workflow_name",
            }
            case.workflow_snapshot_json = snapshot
            case.save(using=alias, update_fields=["workflow_snapshot_json"])


class Migration(migrations.Migration):
    dependencies = [
        ("verifications", "0024_repair_incomplete_decision_contracts"),
        ("workflows", "0006_repair_legacy_workflow_names"),
    ]
    operations = [migrations.RunPython(repair, migrations.RunPython.noop)]
