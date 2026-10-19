from django.db import migrations, models
from django.utils import timezone
from django.db.migrations.recorder import MigrationRecorder


def clear_legacy_placeholder_counts(apps, schema_editor):
    alias = schema_editor.connection.alias
    applied = (
        MigrationRecorder(schema_editor.connection)
        .migration_qs.filter(
            app="biometrics", name="0005_selfiecapture_face_detection_evidence"
        )
        .values_list("applied", flat=True)
        .first()
    )
    if applied is None:
        raise RuntimeError("Face evidence migration application time is unavailable.")
    # Only the old default-one cohort, without any detection attribution, is
    # corrected. Preserve later captures and attributable historical analysis.
    apps.get_model("biometrics", "SelfieCapture").objects.using(alias).filter(
        created_at__lt=applied,
        face_count=1,
        face_detection_confidence__isnull=True,
        face_detection_model_name="",
        face_detection_model_version="",
    ).update(
        face_count=None,
        face_detection_correction_json={
            "kind": "legacy_default_one",
            "previous_face_count": 1,
            "reason": "Default count had no recorded detection provenance.",
            "source_migration": "biometrics.0006_clear_legacy_placeholder_face_counts",
            "cohort_before": applied.isoformat(),
            "corrected_at": timezone.now().isoformat(),
        },
    )


class Migration(migrations.Migration):
    dependencies = [("biometrics", "0005_selfiecapture_face_detection_evidence")]
    operations = [
        migrations.AddField(
            model_name="selfiecapture",
            name="face_detection_correction_json",
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.RunPython(
            clear_legacy_placeholder_counts, migrations.RunPython.noop
        ),
    ]
