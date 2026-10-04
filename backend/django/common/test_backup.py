import io
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from common.backup import (
    BackupError,
    encrypt_stream,
    decrypt_file,
    quiesced,
    load_backup_key,
    restore_backup,
)
from common.storage import get_object_storage_media_bucket_name


class EncryptedBackupTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = os.urandom(32)

    def test_stream_roundtrip_handles_multiple_chunks_without_plaintext_archive(self):
        payload = b"synthetic-document-evidence" * 100000
        encrypted = self.root / "encrypted"
        expected = encrypt_stream(
            io.BytesIO(payload), encrypted, self.key, "backup-id/object"
        )
        self.assertNotIn(b"synthetic-document-evidence", encrypted.read_bytes())
        target = self.root / "target"
        actual = decrypt_file(encrypted, target, self.key, "backup-id/object")
        self.assertEqual(expected, actual)
        self.assertEqual(target.read_bytes(), payload)
        self.assertEqual(encrypted.stat().st_mode & 0o777, 0o600)

    def test_tampering_wrong_key_context_and_truncation_reject_plaintext(self):
        original = self.root / "original"
        encrypt_stream(io.BytesIO(b"synthetic-secret"), original, self.key, "backup/a")
        encrypted = original.read_bytes()
        cases = [
            (encrypted[:-1], self.key, "backup/a"),
            (
                encrypted[:20] + bytes([encrypted[20] ^ 1]) + encrypted[21:],
                self.key,
                "backup/a",
            ),
            (encrypted, os.urandom(32), "backup/a"),
            (encrypted, self.key, "backup/b"),
            (encrypted + b"suffix", self.key, "backup/a"),
        ]
        for index, (data, key, context) in enumerate(cases):
            source = self.root / str(index)
            source.write_bytes(data)
            target = self.root / (str(index) + "-plaintext")
            with self.assertRaises(BackupError):
                decrypt_file(source, target, key, context)
            self.assertFalse(target.exists())

    def test_resume_runs_after_partial_quiesce_failure(self):
        with patch(
            "common.backup.run_hook", side_effect=[RuntimeError("failed"), None]
        ) as hook:
            with self.assertRaises(RuntimeError):
                with quiesced(["pause"], ["resume"]):
                    self.fail("quiesce failure must not create backup")
            self.assertEqual(hook.call_count, 2)
            self.assertEqual(hook.call_args.args, (["resume"],))

    def test_backup_requires_both_hooks(self):
        with self.assertRaises(BackupError):
            with quiesced(["pause"], None):
                pass

    def test_weak_key_file_permissions_are_rejected(self):
        key = self.root / "key"
        key.write_text("invalid")
        key.chmod(0o644)
        with patch.dict(os.environ, {"IDENTITYCORE_BACKUP_KEY_FILE": str(key)}):
            with self.assertRaisesMessage(BackupError, "only to its owner"):
                load_backup_key()

    def test_restore_requires_isolation_before_reading_source(self):
        with patch.dict(os.environ, {"IDENTITYCORE_RESTORE_ISOLATED": "0"}):
            with self.assertRaisesMessage(BackupError, "isolated"):
                restore_backup("missing", self.root)

    @override_settings(OBJECT_STORAGE_MEDIA_BUCKET="isolated-media")
    def test_isolated_restore_ignores_restored_production_storage_override(self):
        with patch.dict(os.environ, {"IDENTITYCORE_RESTORE_ISOLATED": "1"}), patch(
            "common.storage._runtime_setting"
        ) as runtime:
            self.assertEqual(get_object_storage_media_bucket_name(), "isolated-media")
            runtime.assert_not_called()

    def test_restore_authenticates_all_files_before_database_or_object_writes(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        backup_id = "a" * 32
        directory = self.root / backup_id
        directory.mkdir()
        cipher = directory / "database.enc"
        metadata = encrypt_stream(
            io.BytesIO(b"fake dump"), cipher, self.key, backup_id + "/database.enc"
        )
        data = bytearray(cipher.read_bytes())
        data[-1] ^= 1
        cipher.write_bytes(data)
        manifest = {
            "backup_id": backup_id,
            "database_name": "source",
            "buckets": {"media": "source-media"},
            "database": metadata,
            "files": [],
        }
        client = MagicMock()
        client.list_objects_v2.return_value = {"KeyCount": 0}
        fake_connection = MagicMock()
        fake_connection.introspection.table_names.return_value = []
        fake_settings = SimpleNamespace(
            DATABASES={"default": {"NAME": "synthetic_restore"}}
        )
        with patch.dict(os.environ, {"IDENTITYCORE_RESTORE_ISOLATED": "1"}), patch(
            "common.backup.connection", fake_connection
        ), patch("common.backup.settings", fake_settings), patch(
            "common.backup.load_backup_key", return_value=self.key
        ), patch(
            "common.backup.read_manifest", return_value=manifest
        ), patch(
            "common.backup.storage_buckets", return_value={"media": "target-media"}
        ), patch(
            "common.backup.get_object_storage_client", return_value=client
        ), patch(
            "common.backup.subprocess.run"
        ) as run:
            with self.assertRaisesMessage(BackupError, "authentication"):
                restore_backup(directory, self.root)
            client.put_object.assert_not_called()
            run.assert_not_called()
