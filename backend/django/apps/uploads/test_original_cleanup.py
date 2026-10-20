"""Regression coverage for legacy PUT objects after immutable finalization."""

from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.uploads.original_cleanup import cleanup_original_upload
from apps.uploads.tasks import cleanup_expired_uploads_task
from apps.uploads import tests as fixtures
from apps.verifications.models import RetentionLegalHold


@override_settings(OBJECT_STORAGE_TEMP_BUCKET="temporary")
class OriginalUploadCleanupTests(TransactionTestCase):
    setUp = fixtures.UploadRetentionTaskTests.setUp

    def upload(self, *, expired=True):
        upload = Upload.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            purpose=UploadPurpose.DOCUMENT_CAPTURE,
            storage_key=f"pending/{Upload.objects.count()}",
            mime_type="image/jpeg",
            file_size_bytes=100,
            status=UploadStatus.DELETED,
            deleted_at=timezone.now(),
            expires_at=timezone.now() + timedelta(minutes=-10 if expired else 10),
        )
        original = (
            f"organizations/{self.organization.public_id}/verifications/"
            f"{self.verification.public_id}/documents/{upload.public_id}"
        )
        upload.storage_key = original + ".validated." + "a" * 32
        upload.original_storage_key = original
        upload.save(update_fields=["storage_key", "original_storage_key"])
        return upload

    @patch("apps.uploads.original_cleanup.delete_object")
    def test_legacy_grant_keeps_reference_until_expiry_and_grace(self, delete):
        upload = self.upload(expired=False)
        original = upload.original_storage_key
        delete.side_effect = lambda **kwargs: self.assertFalse(
            connection.in_atomic_block
        )
        self.assertTrue(cleanup_original_upload(upload, immediate=True))
        upload.refresh_from_db()
        self.assertEqual(upload.original_storage_key, original)
        self.assertFalse(cleanup_original_upload(upload))
        self.assertEqual(delete.call_count, 1)
        upload.expires_at = timezone.now() - timedelta(minutes=10)
        upload.save(update_fields=["expires_at"])
        self.assertTrue(cleanup_original_upload(upload))
        upload.refresh_from_db()
        self.assertEqual(upload.original_storage_key, "")
        self.assertFalse(cleanup_original_upload(upload))
        self.assertEqual(delete.call_count, 2)
        delete.assert_called_with(bucket_name="temporary", key=original)

    @patch("apps.uploads.original_cleanup.delete_object")
    def test_failed_source_delete_is_retried_even_for_deleted_upload(self, delete):
        upload = self.upload()
        delete.side_effect = OSError("synthetic storage unavailable")
        self.assertEqual(cleanup_expired_uploads_task(limit=1), 0)
        upload.refresh_from_db()
        self.assertTrue(upload.original_storage_key)
        self.assertIsNotNone(upload.original_cleanup_attempted_at)
        delete.side_effect = None
        self.assertEqual(cleanup_expired_uploads_task(limit=1), 0)
        upload.refresh_from_db()
        self.assertEqual(upload.original_storage_key, "")
        self.assertEqual(delete.call_count, 2)

    @patch("apps.uploads.original_cleanup.delete_object")
    def test_hold_and_unowned_references_never_delete(self, delete):
        upload = self.upload()
        hold = RetentionLegalHold.objects.create(
            tenant=self.tenant, verification=self.verification, reason="incident"
        )
        self.assertFalse(cleanup_original_upload(upload, immediate=True))
        hold.released_at = timezone.now()
        hold.save(update_fields=["released_at"])
        for key in (
            upload.storage_key,
            "organizations/foreign/verifications/foreign/documents/foreign",
        ):
            upload.original_storage_key = key
            upload.save(update_fields=["original_storage_key"])
            self.assertFalse(cleanup_original_upload(upload, immediate=True))
        delete.assert_not_called()

    @patch("apps.uploads.original_cleanup.delete_object")
    def test_failed_oldest_reference_does_not_starve_next_upload(self, delete):
        first, second = self.upload(), self.upload()
        delete.side_effect = OSError("synthetic storage unavailable")
        cleanup_expired_uploads_task(limit=1)
        delete.side_effect = None
        cleanup_expired_uploads_task(limit=1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(first.original_storage_key)
        self.assertEqual(second.original_storage_key, "")

    def test_populated_migration_recovers_only_generated_original_references(self):
        from django.db.migrations.executor import MigrationExecutor

        generated = self.upload()
        arbitrary = self.upload()
        arbitrary.storage_key = "unknown/private.validated." + "a" * 32
        arbitrary.save(update_fields=["storage_key"])
        expected = generated.original_storage_key
        executor = MigrationExecutor(connection)
        try:
            executor.migrate(
                [("uploads", "0006_upload_capture_method_upload_capture_receipt")]
            )
            executor = MigrationExecutor(connection)
            executor.migrate([("uploads", "0007_original_upload_cleanup")])
            generated.refresh_from_db()
            arbitrary.refresh_from_db()
            self.assertEqual(generated.original_storage_key, expected)
            self.assertEqual(arbitrary.original_storage_key, "")
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
