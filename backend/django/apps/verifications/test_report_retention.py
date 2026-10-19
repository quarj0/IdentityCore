from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.verifications import tests as fixtures
from apps.verifications.models import Verification, RetentionLegalHold
from apps.verifications.evidence import (
    build_verification_evidence_storage_key,
    build_verification_evidence_pdf_storage_key,
    ensure_verification_evidence_report,
    download_verification_evidence_object,
)
from apps.verifications.tasks import cleanup_retained_media_task
from apps.verifications.report_retention import RETIRED
from apps.verification_subjects.services import request_subject_deletion
from rest_framework.exceptions import NotFound


@override_settings(OBJECT_STORAGE_EVIDENCE_BUCKET="audit-evidence")
class EvidenceReportRetentionTests(TestCase):
    setUp = fixtures.VerificationOperationsTaskTests.setUp

    def _case(self, *, days=31, reports=True):
        case = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Synthetic retention",
            status="verified",
            completed_at=timezone.now() - timedelta(days=days),
            expires_at=timezone.now() - timedelta(days=days),
            policy_snapshot_json={"media_retention_days": 30},
        )
        if reports:
            case.metadata_json = {
                "evidence_report_storage_key": build_verification_evidence_storage_key(
                    case
                ),
                "evidence_report_pdf_storage_key": build_verification_evidence_pdf_storage_key(
                    case
                ),
                "evidence_report_encrypted": True,
                "evidence_report_pdf_encrypted": True,
            }
            case.save(update_fields=["metadata_json"])
        return case

    def test_subject_deletion_keeps_report_tracking_and_partial_deletion_retries(self):
        case = self._case()
        original = dict(case.metadata_json)
        request_subject_deletion(subject=self.subject)
        case.refresh_from_db()
        for key, value in original.items():
            self.assertEqual(case.metadata_json[key], value)

        def delete(**kwargs):
            if kwargs["key"].endswith(".pdf"):
                raise TimeoutError("Synthetic storage outage")

        with patch(
            "apps.verifications.report_retention.delete_object", side_effect=delete
        ) as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            self.assertEqual(storage.call_count, 2)
        case.refresh_from_db()
        self.assertNotIn("evidence_report_storage_key", case.metadata_json)
        self.assertEqual(
            case.metadata_json["evidence_report_pdf_storage_key"],
            original["evidence_report_pdf_storage_key"],
        )
        self.assertIn(RETIRED, case.metadata_json)
        self.assertIsNone(case.media_cleanup_completed_at)
        with patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            storage.assert_called_once_with(
                bucket_name="audit-evidence",
                key=original["evidence_report_pdf_storage_key"],
            )
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
        case.refresh_from_db()
        self.assertIsNotNone(case.media_cleanup_completed_at)
        self.assertEqual(set(case.metadata_json), {RETIRED})

    def test_retired_report_cannot_be_regenerated_or_downloaded(self):
        case = self._case()
        with patch("apps.verifications.report_retention.delete_object"):
            cleanup_retained_media_task(limit=1)
        case.refresh_from_db()
        with patch("apps.verifications.evidence.put_object_bytes") as write, patch(
            "apps.verifications.evidence.get_object_bytes"
        ) as read:
            self.assertIsNone(ensure_verification_evidence_report(case))
            with self.assertRaises(NotFound):
                download_verification_evidence_object(case)
            write.assert_not_called()
            read.assert_not_called()
        client = APIClient()
        client.force_authenticate(self.user)
        for suffix in (
            "evidence-report",
            "evidence-report/download",
            "evidence-report/download.pdf",
        ):
            self.assertEqual(
                client.get(
                    f"/api/v1/verifications/{case.public_id}/{suffix}"
                ).status_code,
                404,
            )

    def test_invalid_reference_and_unconfigured_storage_keep_retryable_pointers(self):
        case = self._case()
        original = dict(case.metadata_json)
        with patch(
            "apps.verifications.report_retention.get_object_storage_evidence_bucket_name",
            return_value="",
        ), patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
            storage.assert_not_called()
        case.refresh_from_db()
        self.assertEqual(
            case.metadata_json["evidence_report_storage_key"],
            original["evidence_report_storage_key"],
        )
        self.assertIsNone(case.media_cleanup_completed_at)
        case.metadata_json = {
            "evidence_report_storage_key": "organizations/foreign/verifications/foreign/reports/verification-report.json"
        }
        case.save(update_fields=["metadata_json"])
        with patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
            storage.assert_not_called()
        case.refresh_from_db()
        self.assertIn("foreign", case.metadata_json["evidence_report_storage_key"])

    def test_active_hold_preserves_reports_until_released(self):
        case = self._case()
        hold = RetentionLegalHold.objects.create(
            tenant=self.tenant, verification=case, reason="Synthetic hold"
        )
        with patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
            storage.assert_not_called()
        case.refresh_from_db()
        self.assertNotIn(RETIRED, case.metadata_json)
        hold.released_at = timezone.now()
        hold.save(update_fields=["released_at"])
        with patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            self.assertEqual(storage.call_count, 2)

    def test_failed_oldest_case_does_not_monopolize_cleanup(self):
        oldest, newer = self._case(days=45), self._case(days=31)
        fail = True

        def delete(**kwargs):
            if fail and oldest.public_id in kwargs["key"]:
                raise TimeoutError("Synthetic unavailable report")

        with patch(
            "apps.verifications.report_retention.delete_object", side_effect=delete
        ):
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            newer.refresh_from_db()
            self.assertIsNotNone(newer.media_cleanup_completed_at)
            fail = False
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
        oldest.refresh_from_db()
        self.assertIsNotNone(oldest.media_cleanup_completed_at)

    def test_partial_generation_is_tracked_before_object_writes(self):
        case = self._case(days=0, reports=False)
        calls = 0

        def write(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise TimeoutError("Synthetic second-object failure")

        with patch("apps.verifications.evidence.put_object_bytes", side_effect=write):
            with self.assertRaises(TimeoutError):
                ensure_verification_evidence_report(case)
        case.refresh_from_db()
        self.assertIn("evidence_report_storage_key", case.metadata_json)
        self.assertIn("evidence_report_pdf_storage_key", case.metadata_json)
        case.completed_at = timezone.now() - timedelta(days=31)
        case.save(update_fields=["completed_at"])
        with patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            self.assertEqual(storage.call_count, 2)

    def test_stale_export_caller_uses_fresh_subject_snapshot(self):
        case = self._case(days=0)
        stale = Verification.objects.select_related("verification_subject").get(
            pk=case.pk
        )
        private_name = stale.verification_subject.full_name
        request_subject_deletion(subject=self.subject)
        with patch("apps.verifications.evidence.put_object_bytes") as write:
            ensure_verification_evidence_report(stale)
        import json

        payload = json.loads(write.call_args_list[0].kwargs["content"])
        self.assertEqual(
            payload["verification_subject"]["full_name"], "Deleted subject"
        )
        self.assertNotIn(
            private_name, write.call_args_list[0].kwargs["content"].decode()
        )

    @override_settings(
        TENANT_STORAGE_DESTINATIONS={
            "audit-old-evidence": "eu-west-1",
            "audit-new-evidence": "eu-west-1",
        }
    )
    def test_retained_route_still_selects_its_original_bucket(self):
        from common.tenant_storage import configure_route

        configure_route(self.tenant, "sandbox", "audit-old-evidence", "eu-west-1")
        self._case()
        configure_route(self.tenant, "sandbox", "audit-new-evidence", "eu-west-1")
        with patch("apps.verifications.report_retention.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
        self.assertEqual(
            {call.kwargs["bucket_name"] for call in storage.call_args_list},
            {"audit-old-evidence"},
        )


@override_settings(OBJECT_STORAGE_EVIDENCE_BUCKET="audit-evidence")
class EvidenceReportStorageTransactionTests(TransactionTestCase):
    setUp = fixtures.VerificationOperationsTaskTests.setUp
    _case = EvidenceReportRetentionTests._case

    def test_report_storage_write_and_retention_delete_run_outside_sql(self):
        case = self._case(days=0, reports=False)

        def storage(**kwargs):
            self.assertFalse(connection.in_atomic_block)

        with patch("apps.verifications.evidence.put_object_bytes", side_effect=storage):
            self.assertIsNotNone(ensure_verification_evidence_report(case))
        case.completed_at = timezone.now() - timedelta(days=31)
        case.save(update_fields=["completed_at"])
        with patch(
            "apps.verifications.report_retention.delete_object", side_effect=storage
        ):
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)

    def test_populated_migration_backfills_deadline_without_guessing_invalid_policy(
        self,
    ):
        from django.db.migrations.executor import MigrationExecutor

        case = self._case()
        invalid = self._case(reports=False)
        invalid.policy_snapshot_json = []
        invalid.save(update_fields=["policy_snapshot_json"])
        expected = case.completed_at + timedelta(days=30)
        executor = MigrationExecutor(connection)
        try:
            executor.migrate(
                [("verifications", "0025_repair_legacy_workflow_name_snapshots")]
            )
            executor = MigrationExecutor(connection)
            executor.migrate([("verifications", "0026_media_cleanup_progress")])
            case.refresh_from_db()
            invalid.refresh_from_db()
            self.assertEqual(case.media_cleanup_due_at, expected)
            self.assertIsNone(case.media_cleanup_completed_at)
            self.assertIsNone(invalid.media_cleanup_due_at)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())

    def test_missing_media_storage_does_not_claim_capture_deletion(self):
        from apps.identity_documents.models import IdentityDocument
        from apps.document_captures.models import DocumentCapture

        case = self._case(reports=False)
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=case,
            verification_subject=self.subject,
            document_type_id="passport",
        )
        capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=document,
            storage_key="synthetic/capture",
            captured_at=timezone.now(),
        )
        with patch(
            "apps.verifications.tasks.get_object_storage_media_bucket_name",
            return_value="",
        ), patch("apps.verifications.tasks.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 0)
            storage.assert_not_called()
        capture.refresh_from_db()
        case.refresh_from_db()
        self.assertIsNone(capture.deleted_at)
        self.assertIsNone(case.media_cleanup_completed_at)
        with patch(
            "apps.verifications.tasks.get_object_storage_media_bucket_name",
            return_value="audit-media",
        ), patch("apps.verifications.tasks.delete_object") as storage:
            self.assertEqual(cleanup_retained_media_task(limit=1), 1)
            storage.assert_called_once_with(
                bucket_name="audit-media", key="synthetic/capture"
            )

    def test_revocation_can_finish_with_unreadable_policy_then_deadline_recovers(self):
        case = self._case(days=0, reports=False)
        fresh = Verification.objects.get(pk=case.pk)
        completed = timezone.now()
        with patch(
            "common.fields.decrypt_tenant_json",
            side_effect=ValueError("Synthetic key outage"),
        ):
            fresh.status = "cancelled"
            fresh.completed_at = completed
            fresh.save(update_fields=["status", "completed_at"])
        fresh.refresh_from_db()
        self.assertEqual(fresh.status, "cancelled")
        self.assertIsNone(fresh.media_cleanup_due_at)
        self.assertEqual(cleanup_retained_media_task(limit=1), 0)
        fresh.refresh_from_db()
        self.assertEqual(fresh.media_cleanup_due_at, completed + timedelta(days=30))
