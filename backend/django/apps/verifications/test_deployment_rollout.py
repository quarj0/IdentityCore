import tempfile
from pathlib import Path
from unittest import skipUnless

from django.db import connection, migrations, models
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.postgres.operations import AddIndexConcurrently

from apps.verifications import test_processing_jobs as fixtures
from apps.verifications.models import ProcessingJob, ProcessingJobType
from apps.verifications.processing_jobs import (
    acquire_processing_job,
    complete_processing_job,
)
from common.rollout_migrations import expand_safe


class DrainProcessingTests(TestCase):
    setUp = fixtures.ProcessingJobRecoveryTests.setUp

    def test_drain_blocks_new_acquisitions_and_preserves_active_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "draining"
            with override_settings(DEPLOYMENT_DRAIN_FILE=str(marker)):
                job = acquire_processing_job(
                    job_type=ProcessingJobType.IDENTITY_DOCUMENT,
                    resource=self.identity_document,
                )
                marker.touch()
                self.assertIsNone(
                    acquire_processing_job(
                        job_type=ProcessingJobType.IDENTITY_DOCUMENT,
                        resource=self.identity_document,
                    )
                )
                job.refresh_from_db()
                self.assertEqual(job.status, "processing")
                self.assertEqual(job.attempt_count, 1)
                complete_processing_job(job)
                self.assertEqual(ProcessingJob.objects.get().status, "completed")

    def test_late_acknowledgement_is_limited_to_durable_processing(self):
        from apps.biometrics.tasks import process_verification_biometrics_task
        from apps.identity_documents.tasks import process_identity_document_task
        from apps.notifications.tasks import deliver_notification_task

        for task in (
            process_verification_biometrics_task,
            process_identity_document_task,
        ):
            self.assertTrue(task.acks_late)
            self.assertTrue(task.reject_on_worker_lost)
        self.assertFalse(deliver_notification_task.acks_late)
        self.assertFalse(deliver_notification_task.reject_on_worker_lost)

    def test_migration_gate_rejects_operations_that_break_old_code(self):
        self.assertTrue(
            expand_safe(
                migrations.AddField(
                    "fixture", "extra", models.CharField(max_length=32, null=True)
                )
            )
        )
        self.assertTrue(
            expand_safe(
                migrations.AddField(
                    "fixture", "extra", models.IntegerField(db_default=0)
                )
            )
        )
        for operation in [
            migrations.RemoveField("fixture", "value"),
            migrations.AddField("fixture", "extra", models.IntegerField(default=0)),
            migrations.AddField(
                "fixture", "extra", models.IntegerField(db_default=0, unique=True)
            ),
            migrations.RunPython(lambda *_: None),
            migrations.AddIndex(
                "fixture", models.Index(fields=["value"], name="blocking_index")
            ),
        ]:
            self.assertFalse(expand_safe(operation))
        self.assertTrue(
            expand_safe(
                AddIndexConcurrently(
                    "fixture", models.Index(fields=["value"], name="concurrent_index")
                )
            )
        )

    def test_implicit_indexes_relationships_and_null_defaults_block_promotion(self):
        for field in [
            models.CharField(max_length=32, null=True, db_index=True),
            models.ForeignKey(
                "verifications.Verification", on_delete=models.CASCADE, null=True
            ),
            models.ForeignKey(
                "verifications.Verification",
                on_delete=models.CASCADE,
                null=True,
                db_index=False,
            ),
            models.IntegerField(db_default=None),
            models.IntegerField(db_default=models.Value(None)),
            models.IntegerField(db_default=models.Value(0)),
        ]:
            with self.subTest(field=type(field).__name__):
                self.assertFalse(
                    expand_safe(migrations.AddField("fixture", "extra", field))
                )


class OldRolloutFixture(models.Model):
    value = models.CharField(max_length=32)

    class Meta:
        app_label = "verifications"
        managed = False
        db_table = "synthetic_rollout_compatibility"


class NewRolloutFixture(models.Model):
    value = models.CharField(max_length=32)
    extra = models.CharField(max_length=32, null=True)

    class Meta:
        app_label = "verifications"
        managed = False
        db_table = "synthetic_rollout_compatibility"


@skipUnless(connection.vendor == "postgresql", "PostgreSQL rollout compatibility")
class PostgreSQLExpandCompatibilityTests(TransactionTestCase):
    def test_old_and_new_code_overlap_and_code_rollback_preserves_new_data(self):
        with connection.schema_editor() as editor:
            editor.create_model(OldRolloutFixture)
        try:
            first = OldRolloutFixture.objects.create(value="before-expand")
            with connection.schema_editor() as editor:
                editor.add_field(
                    OldRolloutFixture, NewRolloutFixture._meta.get_field("extra")
                )
            old_writer = OldRolloutFixture.objects.create(value="old-code-after-expand")
            new_writer = NewRolloutFixture.objects.create(
                value="new-code", extra="retained-evidence"
            )
            self.assertIsNone(NewRolloutFixture.objects.get(pk=first.pk).extra)
            self.assertIsNone(NewRolloutFixture.objects.get(pk=old_writer.pk).extra)
            # Code rollback continues using the expanded schema; no down migration runs.
            OldRolloutFixture.objects.create(value="rollback-code-write")
            self.assertEqual(
                OldRolloutFixture.objects.get(pk=new_writer.pk).value, "new-code"
            )
            self.assertEqual(
                NewRolloutFixture.objects.get(pk=new_writer.pk).extra,
                "retained-evidence",
            )
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(OldRolloutFixture)
