from django.db import migrations


def backfill_workflow_snapshots(apps, schema_editor):
    Verification = apps.get_model("verifications", "Verification")
    WorkflowVersion = apps.get_model("workflows", "WorkflowVersion")

    versions_by_policy_id = {
        version.policy.public_id: version
        for version in WorkflowVersion.objects.select_related(
            "workflow", "policy"
        ).iterator()
    }
    verifications = Verification.objects.exclude(policy_public_id="")
    for verification in verifications.iterator():
        if verification.workflow_snapshot_json:
            continue
        version = versions_by_policy_id.get(verification.policy_public_id)
        if version is None:
            continue
        verification.workflow_snapshot_json = {
            "id": version.public_id,
            "workflow_id": version.workflow.public_id,
            "workflow_name": version.workflow_name,
            "version": version.version,
            "steps": list(version.steps_json),
            "settings": dict(version.settings_json),
            "published_at": version.published_at.isoformat(),
        }
        verification.save(update_fields=["workflow_snapshot_json"])


class Migration(migrations.Migration):
    dependencies = [
        ("verifications", "0016_verificationdecision_proposed_decision"),
        ("workflows", "0004_workflowversion_workflow_name"),
    ]

    operations = [
        migrations.RunPython(backfill_workflow_snapshots, migrations.RunPython.noop),
    ]
